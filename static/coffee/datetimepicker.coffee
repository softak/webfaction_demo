convertDateToUTC = (date) ->
    return new Date(date.getUTCFullYear(),
                    date.getUTCMonth(),
                    date.getUTCDate(),
                    date.getUTCHours(),
                    date.getUTCMinutes(),
                    date.getUTCSeconds())


window.DateTimePicker = class DateTimePicker
    constructor: (options) ->
        @el = $(options.el)
        
        @_timepickerEl = @el.find('.timepicker-control')
        @_datepickerEl = @el.find('.datepicker-control')
        
        @_datepickerEl.datepicker()
        @_timepickerEl.timePicker
            startTime: new Date(0, 0, 0, 0, 0, 0)
            endTime: new Date(0, 0, 0, 23, 59, 0)
            show24Hours: false
            separator: ':'
            step: 60

        @_timepickerObj = @_timepickerEl[0].timePicker
        @_datepickerObj = @_datepickerEl.data('datepicker')
        
        @_timepickerEl.click => @_datepickerObj.hide() # Hack (to hide datepicker when timepicker opens).

        @_timepickerEl.change =>
            time = moment(@_timepickerObj.getTime())
            @currentDatetime.hours(time.hours())
            @currentDatetime.minutes(time.minutes())
            @._updateHelptext()

        @_datepickerEl.change =>
            date = moment(@_datepickerObj.selectedDate)
            @currentDatetime.year(date.year())
            @currentDatetime.month(date.month())
            # NOTE: moment.fn.date is used to set the date of the month,
            # and moment.fn.day is used to set the day of the week.
            @currentDatetime.date(date.date())
            @._updateHelptext()
        
        initial = options.initial
        @.setCurrentDatetime(initial)
        _this = @
        @el.find('.shortcuts').find('[data-timedelta]').click ->
            timedelta = $(this).data('timedelta')
            _this.setCurrentDatetime(initial.clone().add(timedelta))

    _isValid: ->
        now = moment()
        if @currentDatetime.diff(now) < 0
            @_error = 'Please select date in the future'
            return false
        else if @currentDatetime.diff(now, 'days', true) > 60
            @_error = 'Please select date in a 60 days from now'
            return false
        else
            delete @_error
        return true

    _updateHelptext: ->
        if not @._isValid()
           @el.parent().addClass('error').find('.timediff').html(@_error)
        else
            now = moment()
            @el.parent().removeClass('error').find('.timediff').html(@currentDatetime.from(now))

    setCurrentDatetime: (date) ->
        @currentDatetime = moment(date)
        @currentDatetime.seconds(0)
        @._updateHelptext()

        # Make a copy since Date is mutable and can be corrupted by datepicker and timepicker
        dateClone = new Date(date.valueOf())

        # Update datepicker
        @_datepickerObj.selectDate(dateClone)
        @_datepickerObj.update(@_datepickerObj.selectedDateStr)

        # Update timepicker
        @_timepickerObj.setTime(dateClone)

    getCurrentDatetime: (options) ->
        if @._isValid()
            format = options.format or 'YYYY-MM-DD HH:mm:ss'
            if options.inUTC
                momentToFormat = moment(convertDateToUTC(@currentDatetime.toDate()))
            else
                momentToFormat = @currentDatetime
            return momentToFormat.format(format)
        else
            return false
