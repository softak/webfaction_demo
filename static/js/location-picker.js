(function($) {

    if (typeof $.fn.locationPicker === 'function') { return; }

    $.fn.locationPicker = function(method) {
        if (methods[method]) {
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
        } else if (typeof method === 'object' || !method) {
            return methods.init.apply(this, arguments);
        } else {
            $.error('Method ' +  method + ' does not exist on jQuery.locationPicker');
        }
    };

    var methods = {
        init: function() {
            return this.each(function() {
                var $input = $(this);
                if (!$input.is('input:hidden')) { return; }
                makeLocationPickerFrom($input);
            });
        }
    };

    function makeLocationPickerFrom($input) {
        var latitude = $input.data('latitude'),
            longitude = $input.data('longitude');

        var $map = $('<div></div>', { 'class': 'map' });
        $input.after($map);

        var map = new google.maps.Map($map.get(0), {
            center: new google.maps.LatLng(latitude, longitude),
            zoom: 4,
            mapTypeId: google.maps.MapTypeId.ROADMAP
        });
        $input.data('map', map);

        var service = new google.maps.places.PlacesService(map);
        var infowindow = new google.maps.InfoWindow();

        // Location pointer
        var marker = new google.maps.Marker({
            map: map,
            draggable: true,
            animation: google.maps.Animation.DROP,
            position: new google.maps.LatLng(latitude, longitude)
        });
        $input.data('marker', marker);

        function trackPosition(event) {
            var position = marker.getPosition();
            map.panTo(position);
            $input.val('POINT (' + position.lat() + ' ' + position.lng() + ')');
        }

        google.maps.event.addListener(map, 'click', function(event) {
            marker.setPosition(event.latLng);
            trackPosition(event);
        });

        google.maps.event.addListener(marker, 'dragend', trackPosition);
    }

}(jQuery));
