/*
	*************************

	Tick Marks Tests

	*************************

    Verify that the number of tick marks matches what you set
    Verify the tick marks are at the correct intervals


*/
describe("Slider with ticks tests", function() {

	var testSlider;

	it("Should have the number of tick marks you specify", function() {
		testSlider = $("#testSlider1").slider({
			ticks: [100, 200, 300, 400, 500]
		});

		var numTicks = $("#testSlider1").siblings('div.slider').find('.slider-tick').length;
		expect(numTicks).toBe(5);
	});

	it("Should be at the default positions", function() {
		testSlider = $("#testSlider1").slider({
			ticks: [100, 200, 300, 400, 500]
		});

		$("#testSlider1").siblings('div.slider').find('.slider-tick').each(function(i) {
			expect(this.style.left).toBe(100 * i / 4.0 + '%');
		});
	});

	it("Should be at the positions you specify", function() {
		var tickPositions = [0, 10, 20, 30, 100];
		testSlider = $("#testSlider1").slider({
			ticks: [100, 200, 300, 400, 500],
			ticks_positions: tickPositions
		});

		$("#testSlider1").siblings('div.slider').find('.slider-tick').each(function(i) {
			expect(this.style.left).toBe(tickPositions[i] + '%');
		});
	});

	it("Should have the tick labels you specify", function() {
		var tickLabels = ['$0', '$100', '$200', '$300', '$400'];
		testSlider = $("#testSlider1").slider({
			ticks: [100, 200, 300, 400, 500],
		    ticks_labels: tickLabels
		});

		var tickLabelElements = $("#testSlider1").siblings('div.slider').find('.slider-tick-label');
		expect(tickLabelElements.length).toBe(tickLabels.length);
		tickLabelElements.each(function(i) {
			expect(this.innerHTML).toBe(tickLabels[i]);
		});
	});

	it("Should not snap to a tick within tick bounds when using the keyboard navigation", function() {
		testSlider = $("#testSlider1").slider({
			ticks: [100, 200, 300, 400, 500],
			ticks_snap_bounds: 30
		});

		// Focus on handle1
		var handle1 = $("#testSlider1").prev('div.slider').find('.slider-handle');
		handle1.focus();

		// Create keyboard event
		var keyboardEvent = document.createEvent("Events");
		keyboardEvent.initEvent("keydown", true, true);

		var keyPresses = 0;
		handle1.on("keydown", function() {
			keyPresses++;
			var value = $("#testSlider1").slider('getValue');
			expect(value).toBe(100 + keyPresses);
		});

		keyboardEvent.keyCode = keyboardEvent.which = 39; // RIGHT
		for (var i = 0; i < 5; i++) {
			handle1[0].dispatchEvent(keyboardEvent);
		}
	});

	it("Should show the correct tick marks as 'in-selection', according to the `selection` property", function() {
		var options = {
			ticks: [100, 200, 300, 400, 500],
			value: 250,
			selection: 'after'
		},
		$el = $("#testSlider1");

		testSlider = $el.slider(options);
		expect($el.siblings('div.slider').find('.in-selection').length).toBe(3);

		testSlider.slider('destroy');

		options.selection = 'before';
		testSlider = $el.slider(options);
		expect($el.siblings('div.slider').find('.in-selection').length).toBe(2);
	});

	it("Should reverse the tick labels if `reversed` option is set to true", function() {
		var ticks = [100, 200, 300, 400, 500];
		var ticksLabels = ["$100", "$200", "$300", "$400", "$500"];

		// Create reversed slider
		testSlider = $("#testSlider1").slider({
			id: "testSlider1Ref",
			ticks: ticks,
			ticks_labels: ticksLabels,
			ticks_snap_bounds: 30,
			reversed: true
		});

		// Assert that tick marks are reversed
		var tickLabelsFromDOM = $("#testSlider1Ref .slider-tick-label-container")
			.children(".slider-tick-label")
				.map(function() { return $(this).text(); })
				.toArray();

		var reversedTickLabels = ticksLabels.reverse();
		expect(tickLabelsFromDOM).toEqual(reversedTickLabels);
	});

	it("Should reverse the tick labels if `reversed` option is set to true and `ticks_positions` is specified", function() {
		var ticks = [0, 100, 200, 300, 400];
		var ticksLabels = ["$0", "$100", "$200", "$300", "$400"];

		// Create reversed slider
		testSlider = $("#testSlider1").slider({
			id: "testSlider1Ref",
			ticks: ticks,
			ticks_labels: ticksLabels,
			ticks_positions: [0, 30, 70, 90, 100],
			ticks_snap_bounds: 20,
			value: 200,
			reversed: true
		});

		// Assert that tick marks are reversed
		var tickLabelsFromDOM = $("#testSlider1Ref .slider-tick-label-container .slider-tick-label")
			.sort(function(tickLabelElemA, tickLabelElemB) {
				var leftOffsetA = $(tickLabelElemA).position().left;
				var leftOffsetB = $(tickLabelElemB).position().left;
				
				return leftOffsetA - leftOffsetB;
			})
			.map(function() { return $(this).text(); })
			.toArray();

		var reversedTickLabels = ticksLabels.reverse();
		expect(tickLabelsFromDOM).toEqual(reversedTickLabels);
	});

	it("should wrap all of the ticks within a div with classname '.slider-tick-container'", function() {
		// Create the slider with ticks
		var ticks = [0, 100, 200, 300, 400, 600];
		var $sliderDOMRef = $("#testSlider1");

		// Create reversed slider
		testSlider = $sliderDOMRef.slider({
			id: "testSlider1Ref",
			ticks: ticks,
			ticks_positions: [0, 30, 70, 90, 100, 130]
		});
		
		// Assert that the ticks are children of the container element
		var numTicks = $sliderDOMRef.siblings('div.slider').find('.slider-tick-container > .slider-tick').length;
		expect(numTicks).toBe(ticks.length);
	});

	afterEach(function() {
    if(testSlider) {
      testSlider.slider('destroy');
      testSlider = null;
    }
	});
});

describe("Slider min/max settings", function() {
	var $inputSlider;

	afterEach(function() {
		if ($inputSlider) {
			if ($inputSlider instanceof jQuery) {
				$inputSlider.slider('destroy');
			}
			$inputSlider = null;
		}
	});

	it("Should use min/max tick values for min/max settings", function() {
		$inputSlider = $('#testSlider1').slider({
			ticks: [1, 2, 3]
		});

		expect($inputSlider.slider('getAttribute', 'min')).toBe(1);
		expect($inputSlider.slider('getAttribute', 'max')).toBe(3);
	});

	it("Should not overwrite 'min' setting", function() {
		$inputSlider = $('#testSlider1').slider({
			min: 0,
			ticks: [1, 2, 3]
		});

		expect($inputSlider.slider('getAttribute', 'min')).toBe(0);
		expect($inputSlider.slider('getAttribute', 'max')).toBe(3);
	});

	it("Should not overwrite 'max' setting", function() {
		$inputSlider = $('#testSlider1').slider({
			max: 5,
			ticks: [1, 2, 3]
		});

		expect($inputSlider.slider('getAttribute', 'min')).toBe(1);
		expect($inputSlider.slider('getAttribute', 'max')).toBe(5);
	});

	it("Should not overwrite 'min' or max' settings", function() {
		$inputSlider = $('#testSlider1').slider({
			min: 0,
			max: 5,
			ticks: [1, 2, 3]
		});

		expect($inputSlider.slider('getAttribute', 'min')).toBe(0);
		expect($inputSlider.slider('getAttribute', 'max')).toBe(5);
	});

	it("Should ignore the ticks when outside of min/max range", function() {
		$inputSlider = $("#testSlider1").slider({
			ticks: [100, 200, 300, 400, 500],
			min: 15000,
			max: 25000
		});

		expect($inputSlider.slider('getAttribute', 'min')).toBe(15000);
		expect($inputSlider.slider('getAttribute', 'max')).toBe(25000);
	});
});