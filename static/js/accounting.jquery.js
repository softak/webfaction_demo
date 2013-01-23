(function( $ ) {
    $.fn.formatMoney = function() {
        this.each(function() {
          var $this = $(this);
          $this.html(accounting.formatMoney($this.text()));
        });
    };
})( jQuery );
