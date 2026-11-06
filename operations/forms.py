"""
WEEK 9 — Lab C. A form is the paper form, as a web page.

A ModelForm is written from a model, the way the model was written from the table:
Django reads the fields of Customer and builds one input per field. We only list which
fields a clerk may fill in, and add the business rules that a single column cannot hold.

is_valid() runs every check below. Nothing is saved until it says yes. (The check for rule 10
reads the customers table to look for the same email; it writes nothing.)
"""

from django import forms

from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["customer_name", "customer_type", "contact_name", "email", "phone",
                  "credit_limit", "payment_terms", "resale_cert"]
        # customer_id and customer_since are not here: the view fills them in.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():       # Bootstrap's look for every input
            is_select = isinstance(field.widget, forms.Select)
            field.widget.attrs["class"] = "form-select" if is_select else "form-control"

    # One field, one rule. is_valid() calls clean_<field>() for that field.
    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            # Email may be left empty: this version checks only the second half of rule 10
            # (no two customers share an email), not the first (every customer has one).
            return None
        # Rule 10, second half: no two customers share an email. The database cannot enforce it yet
        # (the two Daily Grinds already share one), so the form checks every new or edited customer.
        others = Customer.objects.filter(email__iexact=email)
        if self.instance.pk:                      # editing: do not compare the customer with itself
            others = others.exclude(pk=self.instance.pk)
        if others.exists():
            raise forms.ValidationError("Another customer already uses this email address (rule 10).")
        return email

    # Several fields, one rule. is_valid() calls clean() after the single-field checks.
    def clean(self):
        cleaned = super().clean()
        ctype = cleaned.get("customer_type")
        if ctype == Customer.WHOLESALE:
            # Rule 11: wholesale customers must have a resale certificate on file.
            if not cleaned.get("resale_cert"):
                self.add_error("resale_cert", "A wholesale customer needs a resale certificate (rule 11).")
            # Narrative §1: wholesale accounts buy on credit, so they need a limit.
            if cleaned.get("credit_limit") is None:
                self.add_error("credit_limit", "A wholesale customer needs a credit limit.")
        elif ctype == Customer.RETAIL and cleaned.get("credit_limit") is not None:
            self.add_error("credit_limit", "Retail customers pay at checkout; leave the credit limit empty (rule 6).")
        return cleaned
