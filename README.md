Shopping Domain
===============

Installation
------------

After you install project on the server itself you have to do some more steps.


### Facebook

Set appropriate `FACEBOOK_*` in `settings_local.py`.

### PayPal

In `settings_local.py`:  
Set `PP_API_ENVIRONMENT` to `'sandbox'` or `'production'`.  
Then fill `PP_API_EMAIL`, `PP_API_USERID`, `PP_API_PASSWORD`, `PP_API_SIGNATURE` and `PP_API_APPLICATION_ID` using 
the credentials given you from PayPal.  
**Note**: if `PP_API_ENVIRONMENT` is `'sandbox'`, `PP_API_APPLICATION_ID` must be `'APP-80W284485P519543T'`,
this is common id for all sandbox applications.