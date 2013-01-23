from django.forms.fields import FileField, ImageField
from django.forms.widgets import FileInput

class MultiFileInput(FileInput):
    
    def value_from_datadict(self, data, files, name):
        if files:
            return files.getlist(name)
        else:
            return []

    def __init__(self, *args, **kwargs):
        super(MultiFileInput, self).__init__(*args, **kwargs)
        self.attrs.update({ 'multiple': '' })


class MultipleFileField(FileField):
    
    widget = MultiFileInput 

    def to_python(self, data):
        return [super(MultipleFileField, self).to_python(datum) for datum in data]


class MultipleImageField(ImageField):
    
    widget = MultiFileInput 

    def to_python(self, data):
        return [super(MultipleImageField, self).to_python(datum) for datum in data]
