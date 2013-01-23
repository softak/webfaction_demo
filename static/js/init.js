$(function() {
    $(document).tooltip({ selector: "a[rel=tooltip]" });
    $('.money').formatMoney();

    $('.ajaxy').each(function() {
        var $ajaxy = $(this);
        $ajaxy.click(function() {
          $.get($ajaxy.attr('href'), function(data) {
              $ajaxy.parent().html(data.message);
          });
          return false;
        });
    });
});
