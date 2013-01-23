// usage: log('inside coolFunc', this, arguments);
// paulirish.com/2009/log-a-lightweight-wrapper-for-consolelog/
window.log = function(){
  log.history = log.history || [];   // store logs to an array for reference
  log.history.push(arguments);
  if(this.console) {
    arguments.callee = arguments.callee.caller;
    var newarr = [].slice.call(arguments);
    (typeof console.log === 'object' ? log.apply.call(console.log, console, newarr) : console.log.apply(console, newarr));
  }
};

// make it safe to use console.log always
(function(b){function c(){}for(var d="assert,clear,count,debug,dir,dirxml,error,exception,firebug,group,groupCollapsed,groupEnd,info,log,memoryProfile,memoryProfileEnd,profile,profileEnd,table,time,timeEnd,timeStamp,trace,warn".split(","),a;a=d.pop();){b[a]=b[a]||c}})((function(){try
{console.log();return window.console;}catch(err){return window.console={};}})());


getTemplate = function(id) {
    return _.template($('#' + id).text());
}

var CycledList = function(list) {
    this._index = undefined;
    this._list = list;
};

CycledList.prototype.push = function(el) {
    this._list.push(el);
};

CycledList.prototype.next = function() {
    this._index = (this._index + 1) % this._list.length;
    return this._list[this._index];
};

CycledList.prototype.prev = function() {
    this._index = this._index === 0 ? this._list.length - 1 : this._index - 1;
    return this._list[this._index];
};

CycledList.prototype.setCurrent = function(el) {
    if (this._list[this._index] != el) {
        var i = 0, found = false;
        while (!found) {
            if (this._list[i] === el) {
                this._index = i;
                found = true;
            }
            i++;
        }
    }
};


AjaxForm = function(o) {
    this._form = o.form;
    this._form.submit(_.bind(this._submit, this));
    this._action = this._form.attr('action');
    this._method = this._form.attr('method');
    this.o = o;
    this._additionalData = o.additionalData || { };

    var that = this;
    _(this._additionalData).each(function(value, key) {
        var o = $('<input></input>', { type: 'hidden', name: key, value: value });
        $(that._form).append(o);
    });
    
    this._resetFunctions = [];
};

AjaxForm.prototype._submit = function() {
    if (this.o.onSubmit) {
        this.o.onSubmit();
    }
    
    $.ajax({
      url: this._action,
      type: this._method || 'post',
      data: this._form.serialize(),

      error: _.bind(function(jqXHR, cont) {
          if (jqXHR.status == 400) {
              this._onError($.parseJSON(jqXHR.responseText));
          }
      }, this),

      success: _.bind(function(response, _, jqXHR) {
        if (this.o.onSuccess) {
            this.o.onSuccess(response, jqXHR);
        }
      }, this)
    });


    while (this._resetFunctions.length > 0) {
        this._resetFunctions.pop().apply();
    }
    return false;
};

AjaxForm.prototype._onError = function(errors) {
    // response.errors supposed to be standard Django errors dictionary
    $.each(errors, _.bind(function(name, errors) {
        // Get field to the error state
        var inputDiv = $('[name=' + name + ']', this._form).parents('.input:first');
        inputDiv.parents('div:first').addClass('error');
        var error = $('<span></span>', { 'class': 'error-text help-inline',
                                         'html': errors[0] });
        inputDiv.append(error);
        
        // Function that removes error state
        this._resetFunctions.push(function() {
            error.remove();
            inputDiv.parents('div:first').removeClass('error');
        });
    }, this));

    if (this.o.onError) {
        this.o.onError(errors);
    }
};


(function($) {
    // $.fn.resize = function(maxSize) {
    //     return this.each(function(i) {
    //         var h, w;
    //         if ($(this).height() > $(this).width()) {
    //             h = maxSize;
    //             w = Math.ceil($(this).width() / $(this).height() * maxSize);
    //         } else {
    //             h = Math.ceil($(this).height() / $(this).width() * maxSize);
    //             w = maxSize;
    //         }
    //         $(this).css({ height: h, width: w });
    //     });
    // };
    //
    jQuery.extend({
        stringify  : function stringify(obj) {
            var t = typeof (obj);
            if (t != "object" || obj === null) {
                // simple data type
                if (t == "string") obj = '"' + obj + '"';
                return String(obj);
            } else {
                // recurse array or object
                var n, v, json = [], arr = (obj && obj.constructor == Array);

                for (n in obj) {
                    v = obj[n];
                    t = typeof(v);
                    if (obj.hasOwnProperty(n)) {
                        if (t == "string") v = '"' + v + '"'; else if (t == "object" && v !== null) v = jQuery.stringify(v);
                        json.push((arr ? "" : '"' + n + '":') + String(v));
                    }
                }
                return (arr ? "[" : "{") + String(json) + (arr ? "]" : "}");
            }
        }
    });
})(jQuery);
