/* test-code */
if (typeof module === "object" && typeof module.exports === "object") {
  var jsdom = require("jsdom");
  var JSDOM = jsdom.JSDOM;
  var $ = require('jquery')((new JSDOM('<!DOCTYPE html><p>Hello world</p>')).window);
}
/* end-test-code */
/**
 * Color manipulation helper class
 *
 * @param {Object|String} [val]
 * @param {Object} [predefinedColors]
 * @param {String|null} [fallbackColor]
 * @param {String|null} [fallbackFormat]
 * @param {Boolean} [hexNumberSignPrefix]
 * @constructor
 */
var Color = function(
  val, predefinedColors, fallbackColor, fallbackFormat, hexNumberSignPrefix) {
  this.fallbackValue = fallbackColor ?
    (
      (typeof fallbackColor === 'string') ?
      this.parse(fallbackColor) :
      fallbackColor
    ) :
    null;

  this.fallbackFormat = fallbackFormat ? fallbackFormat : 'rgba';

  this.hexNumberSignPrefix = hexNumberSignPrefix === true;

  this.value = this.fallbackValue;

  this.origFormat = null; // original string format

  this.predefinedColors = predefinedColors ? predefinedColors : {};

  // We don't want to share aliases across instances so we extend new object
  this.colors = $.extend({}, Color.webColors, this.predefinedColors);

  if (val) {
    if (typeof val.h !== 'undefined') {
      this.value = val;
    } else {
      this.setColor(String(val));
    }
  }

  if (!this.value) {
    // Initial value is always black if no arguments are passed or val is empty
    this.value = {
      h: 0,
      s: 0,
      b: 0,
      a: 1
    };
  }
};

Color.webColors = { // 140 predefined colors from the HTML Colors spec
  "aliceblue": "f0f8ff",
  "antiquewhite": "faebd7",
  "aqua": "00ffff",
  "aquamarine": "7fffd4",
  "azure": "f0ffff",
  "beige": "f5f5dc",
  "bisque": "ffe4c4",
  "black": "000000",
  "blanchedalmond": "ffebcd",
  "blue": "0000ff",
  "blueviolet": "8a2be2",
  "brown": "a52a2a",
  "burlywood": "deb887",
  "cadetblue": "5f9ea0",
  "chartreuse": "7fff00",
  "chocolate": "d2691e",
  "coral": "ff7f50",
  "cornflowerblue": "6495ed",
  "cornsilk": "fff8dc",
  "crimson": "dc143c",
  "cyan": "00ffff",
  "darkblue": "00008b",
  "darkcyan": "008b8b",
  "darkgoldenrod": "b8860b",
  "darkgray": "a9a9a9",
  "darkgreen": "006400",
  "darkkhaki": "bdb76b",
  "darkmagenta": "8b008b",
  "darkolivegreen": "556b2f",
  "darkorange": "ff8c00",
  "darkorchid": "9932cc",
  "darkred": "8b0000",
  "darksalmon": "e9967a",
  "darkseagreen": "8fbc8f",
  "darkslateblue": "483d8b",
  "darkslategray": "2f4f4f",
  "darkturquoise": "00ced1",
  "darkviolet": "9400d3",
  "deeppink": "ff1493",
  "deepskyblue": "00bfff",
  "dimgray": "696969",
  "dodgerblue": "1e90ff",
  "firebrick": "b22222",
  "floralwhite": "fffaf0",
  "forestgreen": "228b22",
  "fuchsia": "ff00ff",
  "gainsboro": "dcdcdc",
  "ghostwhite": "f8f8ff",
  "gold": "ffd700",
  "goldenrod": "daa520",
  "gray": "808080",
  "green": "008000",
  "greenyellow": "adff2f",
  "honeydew": "f0fff0",
  "hotpink": "ff69b4",
  "indianred": "cd5c5c",
  "indigo": "4b0082",
  "ivory": "fffff0",
  "khaki": "f0e68c",
  "lavender": "e6e6fa",
  "lavenderblush": "fff0f5",
  "lawngreen": "7cfc00",
  "lemonchiffon": "fffacd",
  "lightblue": "add8e6",
  "lightcoral": "f08080",
  "lightcyan": "e0ffff",
  "lightgoldenrodyellow": "fafad2",
  "lightgrey": "d3d3d3",
  "lightgreen": "90ee90",
  "lightpink": "ffb6c1",
  "lightsalmon": "ffa07a",
  "lightseagreen": "20b2aa",
  "lightskyblue": "87cefa",
  "lightslategray": "778899",
  "lightsteelblue": "b0c4de",
  "lightyellow": "ffffe0",
  "lime": "00ff00",
  "limegreen": "32cd32",
  "linen": "faf0e6",
  "magenta": "ff00ff",
  "maroon": "800000",
  "mediumaquamarine": "66cdaa",
  "mediumblue": "0000cd",
  "mediumorchid": "ba55d3",
  "mediumpurple": "9370d8",
  "mediumseagreen": "3cb371",
  "mediumslateblue": "7b68ee",
  "mediumspringgreen": "00fa9a",
  "mediumturquoise": "48d1cc",
  "mediumvioletred": "c71585",
  "midnightblue": "191970",
  "mintcream": "f5fffa",
  "mistyrose": "ffe4e1",
  "moccasin": "ffe4b5",
  "navajowhite": "ffdead",
  "navy": "000080",
  "oldlace": "fdf5e6",
  "olive": "808000",
  "olivedrab": "6b8e23",
  "orange": "ffa500",
  "orangered": "ff4500",
  "orchid": "da70d6",
  "palegoldenrod": "eee8aa",
  "palegreen": "98fb98",
  "paleturquoise": "afeeee",
  "palevioletred": "d87093",
  "papayawhip": "ffefd5",
  "peachpuff": "ffdab9",
  "peru": "cd853f",
  "pink": "ffc0cb",
  "plum": "dda0dd",
  "powderblue": "b0e0e6",
  "purple": "800080",
  "red": "ff0000",
  "rosybrown": "bc8f8f",
  "royalblue": "4169e1",
  "saddlebrown": "8b4513",
  "salmon": "fa8072",
  "sandybrown": "f4a460",
  "seagreen": "2e8b57",
  "seashell": "fff5ee",
  "sienna": "a0522d",
  "silver": "c0c0c0",
  "skyblue": "87ceeb",
  "slateblue": "6a5acd",
  "slategray": "708090",
  "snow": "fffafa",
  "springgreen": "00ff7f",
  "steelblue": "4682b4",
  "tan": "d2b48c",
  "teal": "008080",
  "thistle": "d8bfd8",
  "tomato": "ff6347",
  "turquoise": "40e0d0",
  "violet": "ee82ee",
  "wheat": "f5deb3",
  "white": "ffffff",
  "whitesmoke": "f5f5f5",
  "yellow": "ffff00",
  "yellowgreen": "9acd32",
  "transparent": "transparent"
};

Color.prototype = {
  constructor: Color,
  colors: {}, // merged web and predefined colors
  predefinedColors: {},
  /**
   * @return {Object}
   */
  getValue: function() {
    return this.value;
  },
  /**
   * @param {Object} val
   */
  setValue: function(val) {
    this.value = val;
  },
  _sanitizeNumber: function(val) {
    if (typeof val === 'number') {
      return val;
    }
    if (isNaN(val) || (val === null) || (val === '') || (val === undefined)) {
      return 1;
    }
    if (val === '') {
      return 0;
    }
    if (typeof val.toLowerCase !== 'undefined') {
      if (val.match(/^\./)) {
        val = "0" + val;
      }
      return Math.ceil(parseFloat(val) * 100) / 100;
    }
    return 1;
  },
  isTransparent: function(strVal) {
    if (!strVal || !(typeof strVal === 'string' || strVal instanceof String)) {
      return false;
    }
    strVal = strVal.toLowerCase().trim();
    return (strVal === 'transparent') || (strVal.match(/#?00000000/)) || (strVal.match(/(rgba|hsla)\(0,0,0,0?\.?0\)/));
  },
  rgbaIsTransparent: function(rgba) {
    return ((rgba.r === 0) && (rgba.g === 0) && (rgba.b === 0) && (rgba.a === 0));
  },
  // parse a string to HSB
  /**
   * @protected
   * @param {String} strVal
   * @returns {boolean} Returns true if it could be parsed, false otherwise
   */
  setColor: function(strVal) {
    strVal = strVal.toLowerCase().trim();
    if (strVal) {
      if (this.isTransparent(strVal)) {
        this.value = {
          h: 0,
          s: 0,
          b: 0,
          a: 0
        };
        return true;
      } else {
        var parsedColor = this.parse(strVal);
        if (parsedColor) {
          this.value = this.value = {
            h: parsedColor.h,
            s: parsedColor.s,
            b: parsedColor.b,
            a: parsedColor.a
          };
          if (!this.origFormat) {
            this.origFormat = parsedColor.format;
          }
        } else if (this.fallbackValue) {
          // if parser fails, defaults to fallbackValue if defined, otherwise the value won't be changed
          this.value = this.fallbackValue;
        }
      }
    }
    return false;
  },
  setHue: function(h) {
    this.value.h = 1 - h;
  },
  setSaturation: function(s) {
    this.value.s = s;
  },
  setBrightness: function(b) {
    this.value.b = 1 - b;
  },
  setAlpha: function(a) {
    this.value.a = Math.round((parseInt((1 - a) * 100, 10) / 100) * 100) / 100;
  },
  toRGB: function(h, s, b, a) {
    if (arguments.length === 0) {
      h = this.value.h;
      s = this.value.s;
      b = this.value.b;
      a = this.value.a;
    }

    h *= 360;
    var R, G, B, X, C;
    h = (h % 360) / 60;
    C = b * s;
    X = C * (1 - Math.abs(h % 2 - 1));
    R = G = B = b - C;

    h = ~~h;
    R += [C, X, 0, 0, X, C][h];
    G += [X, C, C, X, 0, 0][h];
    B += [0, 0, X, C, C, X][h];

    return {
      r: Math.round(R * 255),
      g: Math.round(G * 255),
      b: Math.round(B * 255),
      a: a
    };
  },
  toHex: function(ignoreFormat, h, s, b, a) {
    if (arguments.length <= 1) {
      h = this.value.h;
      s = this.value.s;
      b = this.value.b;
      a = this.value.a;
    }

    var prefix = '#';
    var rgb = this.toRGB(h, s, b, a);

    if (this.rgbaIsTransparent(rgb)) {
      return 'transparent';
    }

    if (!ignoreFormat) {
      prefix = (this.hexNumberSignPrefix ? '#' : '');
    }

    var hexStr = prefix + (
        (1 << 24) +
        (parseInt(rgb.r) << 16) +
        (parseInt(rgb.g) << 8) +
        parseInt(rgb.b))
      .toString(16)
      .slice(1);

    return hexStr;
  },
  toHSL: function(h, s, b, a) {
    if (arguments.length === 0) {
      h = this.value.h;
      s = this.value.s;
      b = this.value.b;
      a = this.value.a;
    }

    var H = h,
      L = (2 - s) * b,
      S = s * b;
    if (L > 0 && L <= 1) {
      S /= L;
    } else {
      S /= 2 - L;
    }
    L /= 2;
    if (S > 1) {
      S = 1;
    }
    return {
      h: isNaN(H) ? 0 : H,
      s: isNaN(S) ? 0 : S,
      l: isNaN(L) ? 0 : L,
      a: isNaN(a) ? 0 : a
    };
  },
  toAlias: function(r, g, b, a) {
    var c, rgb = (arguments.length === 0) ? this.toHex(true) : this.toHex(true, r, g, b, a);

    // support predef. colors in non-hex format too, as defined in the alias itself
    var original = this.origFormat === 'alias' ? rgb : this.toString(false, this.origFormat);

    for (var alias in this.colors) {
      c = this.colors[alias].toLowerCase().trim();
      if ((c === rgb) || (c === original)) {
        return alias;
      }
    }
    return false;
  },
  RGBtoHSB: function(r, g, b, a) {
    r /= 255;
    g /= 255;
    b /= 255;

    var H, S, V, C;
    V = Math.max(r, g, b);
    C = V - Math.min(r, g, b);
    H = (C === 0 ? null :
      V === r ? (g - b) / C :
      V === g ? (b - r) / C + 2 :
      (r - g) / C + 4
    );
    H = ((H + 360) % 6) * 60 / 360;
    S = C === 0 ? 0 : C / V;
    return {
      h: this._sanitizeNumber(H),
      s: S,
      b: V,
      a: this._sanitizeNumber(a)
    };
  },
  HueToRGB: function(p, q, h) {
    if (h < 0) {
      h += 1;
    } else if (h > 1) {
      h -= 1;
    }
    if ((h * 6) < 1) {
      return p + (q - p) * h * 6;
    } else if ((h * 2) < 1) {
      return q;
    } else if ((h * 3) < 2) {
      return p + (q - p) * ((2 / 3) - h) * 6;
    } else {
      return p;
    }
  },
  HSLtoRGB: function(h, s, l, a) {
    if (s < 0) {
      s = 0;
    }
    var q;
    if (l <= 0.5) {
      q = l * (1 + s);
    } else {
      q = l + s - (l * s);
    }

    var p = 2 * l - q;

    var tr = h + (1 / 3);
    var tg = h;
    var tb = h - (1 / 3);

    var r = Math.round(this.HueToRGB(p, q, tr) * 255);
    var g = Math.round(this.HueToRGB(p, q, tg) * 255);
    var b = Math.round(this.HueToRGB(p, q, tb) * 255);
    return [r, g, b, this._sanitizeNumber(a)];
  },
  /**
   * @param {String} strVal
   * @returns {Object} Object containing h,s,b,a,format properties or FALSE if failed to parse
   */
  parse: function(strVal) {
    if (typeof strVal !== 'string') {
      return this.fallbackValue;
    }
    if (arguments.length === 0) {
      return false;
    }

    var that = this,
      result = false,
      isAlias = (typeof this.colors[strVal] !== 'undefined'),
      values, format;

    if (isAlias) {
      strVal = this.colors[strVal].toLowerCase().trim();
    }

    $.each(this.stringParsers, function(i, parser) {
      var match = parser.re.exec(strVal);
      values = match && parser.parse.apply(that, [match]);
      if (values) {
        result = {};
        format = (isAlias ? 'alias' : (parser.format ? parser.format : that.getValidFallbackFormat()));
        if (format.match(/hsla?/)) {
          result = that.RGBtoHSB.apply(that, that.HSLtoRGB.apply(that, values));
        } else {
          result = that.RGBtoHSB.apply(that, values);
        }
        if (result instanceof Object) {
          result.format = format;
        }
        return false; // stop iterating
      }
      return true;
    });
    return result;
  },
  getValidFallbackFormat: function() {
    var formats = [
      'rgba', 'rgb', 'hex', 'hsla', 'hsl'
    ];
    if (this.origFormat && (formats.indexOf(this.origFormat) !== -1)) {
      return this.origFormat;
    }
    if (this.fallbackFormat && (formats.indexOf(this.fallbackFormat) !== -1)) {
      return this.fallbackFormat;
    }

    return 'rgba'; // By default, return a format that will not lose the alpha info
  },
  /**
   *
   * @param {string} [format] (default: rgba)
   * @param {boolean} [translateAlias] Return real color for pre-defined (non-standard) aliases (default: false)
   * @param {boolean} [forceRawValue] Forces hashtag prefix when getting hex color (default: false)
   * @returns {String}
   */
  toString: function(forceRawValue, format, translateAlias) {
    format = format || this.origFormat || this.fallbackFormat;
    translateAlias = translateAlias || false;

    var c = false;

    switch (format) {
      case 'rgb':
        {
          c = this.toRGB();
          if (this.rgbaIsTransparent(c)) {
            return 'transparent';
          }
          return 'rgb(' + c.r + ',' + c.g + ',' + c.b + ')';
        }
        break;
      case 'rgba':
        {
          c = this.toRGB();
          return 'rgba(' + c.r + ',' + c.g + ',' + c.b + ',' + c.a + ')';
        }
        break;
      case 'hsl':
        {
          c = this.toHSL();
          return 'hsl(' + Math.round(c.h * 360) + ',' + Math.round(c.s * 100) + '%,' + Math.round(c.l * 100) + '%)';
        }
        break;
      case 'hsla':
        {
          c = this.toHSL();
          return 'hsla(' + Math.round(c.h * 360) + ',' + Math.round(c.s * 100) + '%,' + Math.round(c.l * 100) + '%,' + c.a + ')';
        }
        break;
      case 'hex':
        {
          return this.toHex(forceRawValue);
        }
        break;
      case 'alias':
        {
          c = this.toAlias();

          if (c === false) {
            return this.toString(forceRawValue, this.getValidFallbackFormat());
          }

          if (translateAlias && !(c in Color.webColors) && (c in this.predefinedColors)) {
            return this.predefinedColors[c];
          }

          return c;
        }
      default:
        {
          return c;
        }
        break;
    }
  },
  // a set of RE's that can match strings and generate color tuples.
  // from John Resig color plugin
  // https://github.com/jquery/jquery-color/
  stringParsers: [{
    re: /rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*?\)/,
    format: 'rgb',
    parse: function(execResult) {
      return [
        execResult[1],
        execResult[2],
        execResult[3],
        1
      ];
    }
  }, {
    re: /rgb\(\s*(\d*(?:\.\d+)?)\%\s*,\s*(\d*(?:\.\d+)?)\%\s*,\s*(\d*(?:\.\d+)?)\%\s*?\)/,
    format: 'rgb',
    parse: function(execResult) {
      return [
        2.55 * execResult[1],
        2.55 * execResult[2],
        2.55 * execResult[3],
        1
      ];
    }
  }, {
    re: /rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*(\d*(?:\.\d+)?)\s*)?\)/,
    format: 'rgba',
    parse: function(execResult) {
      return [
        execResult[1],
        execResult[2],
        execResult[3],
        execResult[4]
      ];
    }
  }, {
    re: /rgba\(\s*(\d*(?:\.\d+)?)\%\s*,\s*(\d*(?:\.\d+)?)\%\s*,\s*(\d*(?:\.\d+)?)\%\s*(?:,\s*(\d*(?:\.\d+)?)\s*)?\)/,
    format: 'rgba',
    parse: function(execResult) {
      return [
        2.55 * execResult[1],
        2.55 * execResult[2],
        2.55 * execResult[3],
        execResult[4]
      ];
    }
  }, {
    re: /hsl\(\s*(\d*(?:\.\d+)?)\s*,\s*(\d*(?:\.\d+)?)\%\s*,\s*(\d*(?:\.\d+)?)\%\s*?\)/,
    format: 'hsl',
    parse: function(execResult) {
      return [
        execResult[1] / 360,
        execResult[2] / 100,
        execResult[3] / 100,
        execResult[4]
      ];
    }
  }, {
    re: /hsla\(\s*(\d*(?:\.\d+)?)\s*,\s*(\d*(?:\.\d+)?)\%\s*,\s*(\d*(?:\.\d+)?)\%\s*(?:,\s*(\d*(?:\.\d+)?)\s*)?\)/,
    format: 'hsla',
    parse: function(execResult) {
      return [
        execResult[1] / 360,
        execResult[2] / 100,
        execResult[3] / 100,
        execResult[4]
      ];
    }
  }, {
    re: /#?([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})/,
    format: 'hex',
    parse: function(execResult) {
      return [
        parseInt(execResult[1], 16),
        parseInt(execResult[2], 16),
        parseInt(execResult[3], 16),
        1
      ];
    }
  }, {
    re: /#?([a-fA-F0-9])([a-fA-F0-9])([a-fA-F0-9])/,
    format: 'hex',
    parse: function(execResult) {
      return [
        parseInt(execResult[1] + execResult[1], 16),
        parseInt(execResult[2] + execResult[2], 16),
        parseInt(execResult[3] + execResult[3], 16),
        1
      ];
    }
  }],
  colorNameToHex: function(name) {
    if (typeof this.colors[name.toLowerCase()] !== 'undefined') {
      return this.colors[name.toLowerCase()];
    }
    return false;
  }
};
/* test-code */
module.exports = Color;
/* end-test-code */
