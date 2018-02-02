;(function($) {
  "use strict";

  $(function() {

    window.setStatusError = setStatusError;
    window.setStatusSuccess = setStatusSuccess;
    window.clearStatus = clearStatus;

    window.statusRequestHandler = function(selector, onSuccessText, onErrorText) {
      var $error = $(selector);

      return function(err, xhr, body) {
        $error.show();
        if (err) {
          console.log(xhr.responseText);
          try {
            body = JSON.parse(xhr.responseText);
          } catch (e) {}
          setStatusError.call($error, body.message || onErrorText || err);
        } else {
          setStatusSuccess.call($error, onSuccessText || 'Success!');
        }
      };
    };

    window.statusErrorHandler = function(selector) {
      var $error = $(selector || globalErrorMessageSelector);
      return function(e) {
        clearStatus.call($error);
        setStatusError.call($error, e.message || e);
      };
    };

    var globalErrorMessageSelector = '#global-error-message';
    var $globalErrorMessageSelector = $(globalErrorMessageSelector);
    setCloseListener.call($globalErrorMessageSelector);

    function setCloseListener() {
      var $alert = this;
      $alert.find('.glyphicon-remove').click(function() {
        $alert.fadeOut(function() {
          $alert.hide();
        });
      });
    }

    function setStatusError(error) {
      error = escapeHtml(error.message || error);
      console.error('setting error', error);
      this.removeClass('hide alert-success').addClass('alert-danger').html(error);
      resetMessage.call(this);
    }

    function setStatusSuccess(success) {
      success = escapeHtml(success || 'Success!');
      this.removeClass('hide alert-danger').addClass('alert-success').html(success);
      resetMessage.call(this);
    }

    function clearStatus() {
      this.removeClass('alert-success').removeClass('alert-danger').addClass('hide').html('');
    }

    function resetMessage() {
      var $error = this;
      setTimeout(function() {
        $error.fadeOut(function() {
          clearStatus.call($error);
          $error.show();
        });
      }, 15000);
    }
  });

})(jQuery);