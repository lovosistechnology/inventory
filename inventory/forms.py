from django import forms
from .models import Item, StockMovement

class ItemForm(forms.ModelForm):
    """
    A form to add or edit items in the inventory.
    Automatically maps to the Item model fields.
    """
    class Meta:
        model = Item  # This form is linked to the Item model
        # These are the fields that will appear in the form
        fields = [
            'name', 'created_by_name', 'updated_by_name', 'quantity', 'category', 'stock_status',
            'image'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['created_by_name'].disabled = True
            self.fields['created_by_name'].help_text = 'The original creator name cannot be changed.'
        self.fields['updated_by_name'].label = 'Updated by'
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            elif not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                field.widget.attrs['class'] = 'form-control'


class StockMovementForm(forms.ModelForm):
    performed_by_name = forms.CharField(
        label='Modified by',
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Person name', 'class': 'form-control'}),
    )

    class Meta:
        model = StockMovement
        fields = ['direction', 'quantity', 'client_name', 'performed_by_name']
        widgets = {
            'direction': forms.HiddenInput(),
            'quantity': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'client_name': forms.TextInput(attrs={'placeholder': 'Client name', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.HiddenInput) and 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('client_name'):
            self.add_error('client_name', 'Enter the client name for this stock movement.')
        if not cleaned_data.get('performed_by_name'):
            self.add_error('performed_by_name', 'Enter the name of the person who completed this stock movement.')
        return cleaned_data


