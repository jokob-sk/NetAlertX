describe("Aria-valuetext Tests", function() {
      it("Sets the aria-valuetext to 'formatter' value", function() {
      var textValArrayA = new Array('Monday','Wednesday','Friday');
      var tooltipFormatterA = function(value) {
        var arrActiveValueA = value;
        return textValArrayA[arrActiveValueA-1];
      };
      
      //Formatter is used
      var testSliderA = $("#accessibilitySliderA").slider({
        formatter : tooltipFormatterA
      });
      testSliderA.slider('setValue', 2);
      
      var tooltipMessageA = $("#accessibilitySliderA").prev(".slider").children(".min-slider-handle").attr("aria-valuetext");
      var expectedMessageA = tooltipFormatterA(2);
      expect(tooltipMessageA).toBe(expectedMessageA);

      $("#accessibilitySliderA").slider('destroy');
    });
    
    it("Does not use aria-valuetext if 'formatter' is not used", function() {
    	  
      //Formatter is not used  
      var testSliderB = $("#accessibilitySliderB").slider({});
      testSliderB.slider('setValue', 1);
    
      var ariaValueTextB = $("#accessibilitySliderB").prev(".slider").children(".min-slider-handle").attr("aria-valuetext");
      expect(ariaValueTextB).not.toBeDefined();

      $("#accessibilitySliderB").slider('destroy');
    });
    
    it("aria-valuetext if 'formatter' is used and has min & max value", function() {
      var textValArrayC = new Array('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday');
      var tooltipFormatterC = function(value) {
          if(value[1]){
            var arrActiveValueC0 = value[0];
            var arrActiveValueC1 = value[1];  
            return [ textValArrayC[arrActiveValueC0-1], textValArrayC[arrActiveValueC1-1] ];
          } else {
          	var arrActiveValueC = value;
  			return textValArrayC[arrActiveValueC-1];
          }
      };
      
      //Formatter is used for ranges
      var testSliderC = $("#accessibilitySliderC").slider({
        range: true,
        formatter : tooltipFormatterC
      });
      var valuesToSet = [2,4];
      testSliderC.slider('setValue', valuesToSet);
      var expectedMessageC = tooltipFormatterC([2,4]);
      var ttminMessage = $("#accessibilitySliderC").prev(".slider").children(".min-slider-handle").attr("aria-valuetext");
      var ttmaxMessage = $("#accessibilitySliderC").prev(".slider").children(".max-slider-handle").attr("aria-valuetext");
      expect(ttminMessage).toBe(expectedMessageC[0]);
      expect(ttmaxMessage).toBe(expectedMessageC[1]);

      $('#accessibilitySliderC').slider('destroy');
    });

    describe("Unset 'aria-valuetext' attribute when value can be represented as a number", function() {
      var $testSliderC;
      var dayOfWeek;

      var dayFormatter = function(value) {
        if (value[1]) {
          return [ dayOfWeek[value[0]-1], dayOfWeek[value[1]-1] ];
        }
        return dayOfWeek[value-1];
      };

      beforeEach(function() {
        dayOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

        $testSliderC = $('#accessibilitySliderC').slider({
          id: 'testAccessbilitySlider',
          min: 1,
          max: 7,
          formatter : dayFormatter
        });
      });

      afterEach(function() {
        if ($testSliderC) {
          $testSliderC.slider('destroy');
        }
      });

      it("Should unset 'aria-valuetext' attribute", function() {
        dayOfWeek[0] = '1';

        var valueToSet = 1;
        $testSliderC.slider('setValue', valueToSet);
        var ariaValueText = $('#testAccessbilitySlider').find('.min-slider-handle')[0].getAttribute('aria-valuetext');
        expect(ariaValueText).toBeNull();
      });

      it("Should unset 'aria-valuetext' attributes for range sliders", function() {
        dayOfWeek[0] = '1';
        dayOfWeek[6] = '7';
        $testSliderC.slider('setAttribute', 'range', true);
        $testSliderC.slider('refresh');

        var valuesToSet = [1, 7];
        $testSliderC.slider('setValue', valuesToSet);
        var ariaValueText1 = $('#testAccessbilitySlider').find('.min-slider-handle')[0].getAttribute('aria-valuetext');
        var ariaValueText2 = $('#testAccessbilitySlider').find('.max-slider-handle')[0].getAttribute('aria-valuetext');
        expect(ariaValueText1).toBeNull();
        expect(ariaValueText2).toBeNull();
      });
    });
});
