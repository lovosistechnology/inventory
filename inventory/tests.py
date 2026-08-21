from django.test import TestCase
from django.contrib.auth.models import User

from .models import AuditLog, Item, StockMovement


class AddItemTests(TestCase):
	def test_add_item_persists_creator_and_details(self):
		user = User.objects.create_user(username="owner", password="test-password")
		self.client.force_login(user)

		response = self.client.post(
			"/add/",
			{
				"name": "Laptop",
				"created_by_name": "Alex Manager",
				"quantity": 5,
				"category": "Electronics",
				"stock_status": "in_stock",
			},
		)

		self.assertRedirects(response, "/items/")
		item = Item.objects.get(name="Laptop")
		self.assertEqual(item.created_by_name, "Alex Manager")
		self.assertEqual(item.quantity, 5)
		self.assertEqual(item.category, "Electronics")

	def test_creator_is_preserved_and_updates_are_logged(self):
		creator = User.objects.create_user(username="creator", password="test-password")
		self.client.force_login(creator)
		self.client.post("/add/", {
			"name": "Monitor", "created_by_name": "Jordan Creator", "quantity": 10,
			"category": "Electronics", "stock_status": "in_stock",
		})
		item = Item.objects.get(name="Monitor")

		self.client.post(f"/edit/{item.pk}/", {
			"name": "Updated Monitor", "created_by_name": "Changed Name", "quantity": 10,
			"category": "Electronics", "stock_status": "in_stock",
			"updated_by_name": "Taylor Manager",
		})

		item.refresh_from_db()
		self.assertEqual(item.created_by, creator)
		self.assertEqual(item.created_by_name, "Jordan Creator")
		self.assertEqual(item.updated_by_name, "Taylor Manager")
		self.assertEqual(item.updated_by, creator)
		self.assertEqual(AuditLog.objects.filter(item=item, action="updated").count(), 1)

	def test_stock_movement_updates_quantity_and_logs_client(self):
		user = User.objects.create_user(username="stockkeeper", password="test-password")
		self.client.force_login(user)
		self.client.post("/add/", {
			"name": "Keyboard", "created_by_name": "Stock Creator", "quantity": 10,
			"category": "Electronics", "stock_status": "in_stock",
		})
		item = Item.objects.get(name="Keyboard")

		response = self.client.post(f"/item/{item.pk}/stock/", {
			"direction": "out", "quantity": 3, "client_name": "Northwind Ltd", "performed_by_name": "Sam Warehouse",
		})

		self.assertRedirects(response, f"/item/{item.pk}/")
		item.refresh_from_db()
		self.assertEqual(item.quantity, 7)
		movement = StockMovement.objects.get(item=item)
		self.assertEqual(movement.client_name, "Northwind Ltd")
		self.assertEqual(movement.performed_by_name, "Sam Warehouse")
		self.assertEqual(movement.performed_by, user)
		self.assertEqual(AuditLog.objects.filter(item=item, action="stock").count(), 1)

	def test_add_stock_movement_records_client_and_person(self):
		user = User.objects.create_user(username="receiver", password="test-password")
		self.client.force_login(user)
		self.client.post("/add/", {
			"name": "Mouse", "created_by_name": "Warehouse Lead", "quantity": 2,
			"category": "Electronics", "stock_status": "in_stock",
		})
		item = Item.objects.get(name="Mouse")

		response = self.client.post(f"/item/{item.pk}/stock/", {
			"direction": "in", "quantity": 4, "client_name": "Central Office",
			"performed_by_name": "Jordan Receiver",
		})

		self.assertRedirects(response, f"/item/{item.pk}/")
		movement = StockMovement.objects.get(item=item)
		self.assertEqual(movement.direction, "in")
		self.assertEqual(movement.performed_by_name, "Jordan Receiver")
		self.assertEqual(movement.client_name, "Central Office")

	def test_bulk_delete_removes_selected_items_and_logs_each_deletion(self):
		user = User.objects.create_user(username="manager", password="test-password")
		self.client.force_login(user)
		for name in ("Chair", "Desk"):
			self.client.post("/add/", {
				"name": name, "created_by_name": "Manager", "quantity": 2,
				"category": "Office", "stock_status": "in_stock",
			})
		item_ids = list(Item.objects.values_list("pk", flat=True))

		response = self.client.post("/delete-selected/", {"item_ids": item_ids})

		self.assertRedirects(response, "/items/")
		self.assertEqual(Item.objects.count(), 0)
		self.assertEqual(AuditLog.objects.filter(action="deleted").count(), 2)
		self.assertTrue(all(log.actor == user for log in AuditLog.objects.filter(action="deleted")))


class NavigationTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="navigator", password="test-password")
		self.client.force_login(self.user)

	def test_sidebar_pages_render(self):
		for path in ("/dashboard/", "/items/", "/stock/", "/category-stock/", "/history/"):
			with self.subTest(path=path):
				response = self.client.get(path)
				self.assertEqual(response.status_code, 200)

	def test_stock_update_modal_contains_modified_by_field(self):
		Item.objects.create(
			user=self.user, created_by=self.user, created_by_name="Navigator",
			name="Test item", quantity=5, category="Office", stock_status="in_stock",
		)
		response = self.client.get("/items/")

		self.assertContains(response, 'name="performed_by_name"')
		self.assertContains(response, "Modified by")

	def test_logout_returns_to_login(self):
		response = self.client.get("/logout/")
		self.assertRedirects(response, "/")
		root_response = self.client.get("/")
		self.assertContains(root_response, "Welcome back")


class AuthRedirectTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="testuser", password="test-password123")

	def test_unauthenticated_user_accessing_root_stays_on_root(self):
		response = self.client.get("/")
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "inventory/login.html")

	def test_login_successful_redirects_to_dashboard(self):
		response = self.client.post("/", {"username": "testuser", "password": "test-password123"})
		self.assertRedirects(response, "/dashboard/")

	def test_authenticated_user_accessing_root_redirects_to_dashboard(self):
		self.client.force_login(self.user)
		response = self.client.get("/")
		self.assertRedirects(response, "/dashboard/")

	def test_authenticated_user_accessing_login_alias_redirects_to_dashboard(self):
		self.client.force_login(self.user)
		response = self.client.get("/login/")
		self.assertRedirects(response, "/dashboard/")

	def test_unauthenticated_user_accessing_protected_page_redirects_to_login_root(self):
		response = self.client.get("/dashboard/")
		self.assertRedirects(response, "/?next=/dashboard/")
