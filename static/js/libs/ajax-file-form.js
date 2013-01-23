qq.AjaxFileForm = function(o) {
    qq.UploadHandlerForm.apply(this, arguments);

    if (!o.hasOwnProperty('form')) {
        $.error('qq.UploadHandlerCsrfForm: form option is not specified!');
    }

    this._form = o.form;
    this._resetFunctions = [];

    // Make list of extra fields
    this._fields = $('input', this._form).filter('[type!=submit]')
                                         .filter('[type!=file]');
                                   
    this._options.action = this._form.attr('action');
    this._options.onComplete = _.bind(this._onComplete, this);

    this._form.submit(_.bind(this._onSubmit, this));
};
    
qq.extend(qq.AjaxFileForm.prototype,
          qq.UploadHandlerForm.prototype);

qq.extend(qq.AjaxFileForm.prototype, {

    /* Fix. Original `add` changes name of the fileInput to "qqfile" */
    add: function(fileInput){
        var id = 'qq-upload-handler-iframe' + qq.getUniqueId();       
        this._inputs[id] = fileInput;
        
        if (fileInput.parentNode){
            qq.remove(fileInput);
        }
                
        return id;
    },


    _createForm: function(iframe, params) {
        // Copy to iframe form file input
        var form = qq.UploadHandlerForm.prototype._createForm.apply(this, arguments);

        // Copy extrafields
        _(this._fields).each(function(field) {
            $(form).append($(field).clone());
        });
        return form;
    },


    /* Fix. Because in the Chrome doc.body.innerHTML (which is used in original
     * _getIframeContentJSON) is wrapped with the <pre></pre> tags.
     * It seems like that happens when mime type is the application/json. */
    _getIframeContentJSON: function(iframe){
        var doc = iframe.contentDocument;
        var innerText = $(doc.body).text();
        try {
            response = eval('(' + innerText + ')');
        } catch (err) {
            response = {};
        }
        return response;
    },


    _onSubmit: function() {
        var input = $('[type=file]', this._form);
        /* Clone file input, because `handler.add` removes it from the 
         * original form and places to the iframe form */
        input.replaceWith(input.clone());
        var fileId = this.add(input.get(0));

        if (this._options.onSubmit) {
            this._options.onSubmit();
        }
        this.upload(fileId);

        this._form.get(0).reset();
        while (this._resetFunctions.length > 0) {
            this._resetFunctions.pop().apply();
        }
        return false;
    },


    _onComplete: function(id, filename, response) {
        if (response.hasOwnProperty('errors')) {
            // response.errors supposed to be standard Django errors dictionary
            $.each(response.errors, _.bind(function(name, errors) {
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

            if (this._options.onError) {
                this._options.onError(id, filename, response);
            }
        } else {
            if (this._options.onSuccess) {
                this._options.onSuccess(id, filename, response);
            }
        }
    }

});
