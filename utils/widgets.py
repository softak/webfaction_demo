from django.forms import CheckboxSelectMultiple, ClearableFileInput


class BootstrapCheckboxSelectMultiple(CheckboxSelectMultiple):

    def render(self, name, value, attrs=None, choices=()):
        output = super(BootstrapCheckboxSelectMultiple, self).render(
            name, value, attrs, choices)
        # we don't need ul-li structure
        output = output.replace('<li>', '').replace('</li>', '')\
                       .replace('<ul>', '').replace('</ul>', '')
        # we need class="checkbox" for labels
        output = output.replace('<label', '<label class="checkbox"')
        return output


class BootstrapClearableFileInput(ClearableFileInput):

    template_with_initial = u'%(clear_template)s%(input_text)s: %(input)s'
    template_with_clear = u'<label for="%(clear_checkbox_id)s" class="checkbox">%(clear)s %(clear_checkbox_label)s</label>'
