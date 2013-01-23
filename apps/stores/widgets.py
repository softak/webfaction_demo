from django import forms
from django.utils.safestring import mark_safe
from django.contrib.gis.geometry.backend import Geometry

class LocationWidget(forms.widgets.Widget):
    def __init__(self, *args, **kwargs):
        super(LocationWidget, self).__init__(*args, **kwargs)
        self.inner_widget = forms.widgets.HiddenInput()

    def render(self, name, value, *args, **kwargs):
        if value == '' or value is None:
            value = ''
            lat, lng = -23.815501, 134.307861 # Just some location in Australia
        else:
            # If form doesn't pass validation, value passed to the widget will be a string
            value = Geometry(value)
            lat, lng = value.x, value.y
        html = '<div class="location-picker">'
        html += self.inner_widget.render('%s' % name, None, {
            'id': '%s_id' % name, 
            'value': value,
            'class': 'location',
            'data-latitude': lat,
            'data-longitude': lng
        })
        html += '</div>'
        html += '''
            <script type="text/javascript">
                window.gmapInitialized = function() { $('#%s_id').locationPicker('init'); };
            </script> ''' % name

        return mark_safe(html)


class ZoomWidget(forms.widgets.Widget):
    def __init__(self, *args, **kwargs):
        super(ZoomWidget, self).__init__(*args, **kwargs)
        self.inner_widget = forms.widgets.HiddenInput()

    def render(self, name, value, *args, **kwargs):
        js = '''
            <script type="text/javascript">
                window.gmapInitialized = function() {
                    $('#%(related_map_id)s').locationPicker('init');
                    var map = $('#%(related_map_id)s').data('map');
                    var marker = $('#%(related_map_id)s').data('marker');
                    
                    google.maps.event.addListener(map, 'zoom_changed', function() {
                        var zoomLevel = map.getZoom();
                        $('#%(name)s_id').val(zoomLevel);
                        $('#%(name)s_value').text(zoomLevel);
                        map.setCenter(marker.getPosition()); // always center on location marker
                    });

                    map.setZoom(%(zoom)s);
                };
            </script>
        ''' % { 'name': name,
                'related_map_id': self.related_map_id,
                'zoom': value or 8 }

        html = self.inner_widget.render('%s' % name, None, {
            'id': '%s_id' % name,
            'value': value
        })
        html += '<span id="%s_value"></span>' % name

        return mark_safe(js + html)

class AddressAutocompleteWidget(forms.TextInput):

    def render(self, name, value, *args, **kwargs):
        js = '''
        <script type="text/javascript">
            window.gmapAndAddressInit = function(){
                window.gmapInitialized()
                var geocoder = new google.maps.Geocoder();
                $('input#id_%(name)s').autocomplete({
                    open: function() { $('.ui-menu').width(%(width)d) },
                    source: function(request, response) {
                        geocoder.geocode( {'address': request.term }, 
                            function(results, status) {
                              response($.map(results, function(item) {
                                return {
                                  label:  item.formatted_address,
                                  value: item.formatted_address,
                                  latitude: item.geometry.location.lat(),
                                  longitude: item.geometry.location.lng()
                                }
                              }));
                        })
                      },
                      select: function(event, ui) {
                        var map    = $('#%(location)s_id').data('map');
                        var marker = $('#%(location)s_id').data('marker');
                        var location = new google.maps.LatLng(ui.item.latitude, 
                                                            ui.item.longitude);
                        marker.setPosition(location);
                        map.setCenter(location);
                        map.setZoom(%(zoom)d);
                      }
                });
            }
        </script>
        ''' % {'name':name, 'zoom':15, 'location':'location', 'width':500}
        html = super(AddressAutocompleteWidget, self).render(name, value, 
                                                         *args, **kwargs)
        return html + mark_safe(js)
