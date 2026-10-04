(function (global, factory) {
  typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports, require('three'), require('eventemitter2'), require('jszip'), require('fast-xml-parser'), require('three-nebula'), require('rxjs'), require('protobufjs')) :
  typeof define === 'function' && define.amd ? define(['exports', 'three', 'eventemitter2', 'jszip', 'fast-xml-parser', 'three-nebula', 'rxjs', 'protobufjs'], factory) :
  (global = typeof globalThis !== 'undefined' ? globalThis : global || self, factory(global.gzweb = {}, global.THREE, global.eventemitter2, global.JSZip, global["fast-xml-parser"], global["three-nebula"], global.rxjs, global.protobufjs));
})(this, (function (exports, THREE, eventemitter2, JSZip, fastXmlParser, System, rxjs, protobufjs) { 'use strict';

  function _interopDefaultLegacy (e) { return e && typeof e === 'object' && 'default' in e ? e : { 'default': e }; }

  function _interopNamespace(e) {
    if (e && e.__esModule) return e;
    var n = Object.create(null);
    if (e) {
      Object.keys(e).forEach(function (k) {
        if (k !== 'default') {
          var d = Object.getOwnPropertyDescriptor(e, k);
          Object.defineProperty(n, k, d.get ? d : {
            enumerable: true,
            get: function () { return e[k]; }
          });
        }
      });
    }
    n["default"] = e;
    return Object.freeze(n);
  }

  var THREE__namespace = /*#__PURE__*/_interopNamespace(THREE);
  var JSZip__namespace = /*#__PURE__*/_interopNamespace(JSZip);
  var System__default = /*#__PURE__*/_interopDefaultLegacy(System);

  function _typeof(obj) {
    "@babel/helpers - typeof";

    return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (obj) {
      return typeof obj;
    } : function (obj) {
      return obj && "function" == typeof Symbol && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj;
    }, _typeof(obj);
  }

  function _classCallCheck(instance, Constructor) {
    if (!(instance instanceof Constructor)) {
      throw new TypeError("Cannot call a class as a function");
    }
  }

  function _defineProperties(target, props) {
    for (var i = 0; i < props.length; i++) {
      var descriptor = props[i];
      descriptor.enumerable = descriptor.enumerable || false;
      descriptor.configurable = true;
      if ("value" in descriptor) descriptor.writable = true;
      Object.defineProperty(target, descriptor.key, descriptor);
    }
  }

  function _createClass(Constructor, protoProps, staticProps) {
    if (protoProps) _defineProperties(Constructor.prototype, protoProps);
    if (staticProps) _defineProperties(Constructor, staticProps);
    Object.defineProperty(Constructor, "prototype", {
      writable: false
    });
    return Constructor;
  }

  function _defineProperty(obj, key, value) {
    if (key in obj) {
      Object.defineProperty(obj, key, {
        value: value,
        enumerable: true,
        configurable: true,
        writable: true
      });
    } else {
      obj[key] = value;
    }

    return obj;
  }

  function _inherits(subClass, superClass) {
    if (typeof superClass !== "function" && superClass !== null) {
      throw new TypeError("Super expression must either be null or a function");
    }

    subClass.prototype = Object.create(superClass && superClass.prototype, {
      constructor: {
        value: subClass,
        writable: true,
        configurable: true
      }
    });
    Object.defineProperty(subClass, "prototype", {
      writable: false
    });
    if (superClass) _setPrototypeOf(subClass, superClass);
  }

  function _getPrototypeOf(o) {
    _getPrototypeOf = Object.setPrototypeOf ? Object.getPrototypeOf.bind() : function _getPrototypeOf(o) {
      return o.__proto__ || Object.getPrototypeOf(o);
    };
    return _getPrototypeOf(o);
  }

  function _setPrototypeOf(o, p) {
    _setPrototypeOf = Object.setPrototypeOf ? Object.setPrototypeOf.bind() : function _setPrototypeOf(o, p) {
      o.__proto__ = p;
      return o;
    };
    return _setPrototypeOf(o, p);
  }

  function _isNativeReflectConstruct() {
    if (typeof Reflect === "undefined" || !Reflect.construct) return false;
    if (Reflect.construct.sham) return false;
    if (typeof Proxy === "function") return true;

    try {
      Boolean.prototype.valueOf.call(Reflect.construct(Boolean, [], function () {}));
      return true;
    } catch (e) {
      return false;
    }
  }

  function _assertThisInitialized(self) {
    if (self === void 0) {
      throw new ReferenceError("this hasn't been initialised - super() hasn't been called");
    }

    return self;
  }

  function _possibleConstructorReturn(self, call) {
    if (call && (typeof call === "object" || typeof call === "function")) {
      return call;
    } else if (call !== void 0) {
      throw new TypeError("Derived constructors may only return object or undefined");
    }

    return _assertThisInitialized(self);
  }

  function _createSuper(Derived) {
    var hasNativeReflectConstruct = _isNativeReflectConstruct();

    return function _createSuperInternal() {
      var Super = _getPrototypeOf(Derived),
          result;

      if (hasNativeReflectConstruct) {
        var NewTarget = _getPrototypeOf(this).constructor;

        result = Reflect.construct(Super, arguments, NewTarget);
      } else {
        result = Super.apply(this, arguments);
      }

      return _possibleConstructorReturn(this, result);
    };
  }

  function _superPropBase(object, property) {
    while (!Object.prototype.hasOwnProperty.call(object, property)) {
      object = _getPrototypeOf(object);
      if (object === null) break;
    }

    return object;
  }

  function _get() {
    if (typeof Reflect !== "undefined" && Reflect.get) {
      _get = Reflect.get.bind();
    } else {
      _get = function _get(target, property, receiver) {
        var base = _superPropBase(target, property);

        if (!base) return;
        var desc = Object.getOwnPropertyDescriptor(base, property);

        if (desc.get) {
          return desc.get.call(arguments.length < 3 ? target : receiver);
        }

        return desc.value;
      };
    }

    return _get.apply(this, arguments);
  }

  function _slicedToArray(arr, i) {
    return _arrayWithHoles(arr) || _iterableToArrayLimit(arr, i) || _unsupportedIterableToArray(arr, i) || _nonIterableRest();
  }

  function _arrayWithHoles(arr) {
    if (Array.isArray(arr)) return arr;
  }

  function _iterableToArrayLimit(arr, i) {
    var _i = arr == null ? null : typeof Symbol !== "undefined" && arr[Symbol.iterator] || arr["@@iterator"];

    if (_i == null) return;
    var _arr = [];
    var _n = true;
    var _d = false;

    var _s, _e;

    try {
      for (_i = _i.call(arr); !(_n = (_s = _i.next()).done); _n = true) {
        _arr.push(_s.value);

        if (i && _arr.length === i) break;
      }
    } catch (err) {
      _d = true;
      _e = err;
    } finally {
      try {
        if (!_n && _i["return"] != null) _i["return"]();
      } finally {
        if (_d) throw _e;
      }
    }

    return _arr;
  }

  function _unsupportedIterableToArray(o, minLen) {
    if (!o) return;
    if (typeof o === "string") return _arrayLikeToArray(o, minLen);
    var n = Object.prototype.toString.call(o).slice(8, -1);
    if (n === "Object" && o.constructor) n = o.constructor.name;
    if (n === "Map" || n === "Set") return Array.from(o);
    if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen);
  }

  function _arrayLikeToArray(arr, len) {
    if (len == null || len > arr.length) len = arr.length;

    for (var i = 0, arr2 = new Array(len); i < len; i++) arr2[i] = arr[i];

    return arr2;
  }

  function _nonIterableRest() {
    throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
  }

  function _createForOfIteratorHelper(o, allowArrayLike) {
    var it = typeof Symbol !== "undefined" && o[Symbol.iterator] || o["@@iterator"];

    if (!it) {
      if (Array.isArray(o) || (it = _unsupportedIterableToArray(o)) || allowArrayLike && o && typeof o.length === "number") {
        if (it) o = it;
        var i = 0;

        var F = function () {};

        return {
          s: F,
          n: function () {
            if (i >= o.length) return {
              done: true
            };
            return {
              done: false,
              value: o[i++]
            };
          },
          e: function (e) {
            throw e;
          },
          f: F
        };
      }

      throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
    }

    var normalCompletion = true,
        didErr = false,
        err;
    return {
      s: function () {
        it = it.call(o);
      },
      n: function () {
        var step = it.next();
        normalCompletion = step.done;
        return step;
      },
      e: function (e) {
        didErr = true;
        err = e;
      },
      f: function () {
        try {
          if (!normalCompletion && it.return != null) it.return();
        } finally {
          if (didErr) throw err;
        }
      }
    };
  }

  var AssetError;

  (function (AssetError) {
    AssetError["NOT_FOUND"] = "asset_not_found";
    AssetError["URI_MISSING"] = "asset_uri_missing";
  })(AssetError || (AssetError = {}));
  /**
   * Type that represents a simulation asset that needs to be fetched from a websocket server.
   */


  var Asset = /*#__PURE__*/_createClass(function Asset(uri, cb) {
    _classCallCheck(this, Asset);

    this.uri = uri;
    this.cb = cb;
  });

  /**
   * Given a ThreeJS Object, return all its children as an array.
   * Notes:
   * - We are using getDescendants as a way to maintain legacy code. We should use traverse() whenever possible.
   * - We should discourage its use and move towards using traverse().
   * @param obj The ThreeJS Object to get the descendants of.
   * @param array Optional. An array that will store all the children.
   * @returns An array of the children of the given ThreeJS Object (can be dismissed if the array argument is used).
   */
  function getDescendants(obj) {
    var array = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : [];
    obj.traverse(function (child) {
      // Note: This function is called on the obj as well.
      // Since we just need its children, we filter the original object.
      if (child !== obj) {
        array.push(child);
      }
    });
    return array;
  }
  /**
   * Convert a binary byte array to a base64 string.
   * @param {byte array} buffer - Binary byte array
   * @return Base64 encoded string.
   **/

  function binaryToBase64(buffer) {
    var binary = "";
    var len = buffer.byteLength;

    for (var i = 0; i < len; i++) {
      binary += String.fromCharCode(buffer[i]);
    }

    return window.btoa(binary);
  }
  /**
   * Convert a RGBA encoded uint8array to an image.
   * @param {byte array} array - Binary byte array encoded as RGBA pixels.
   * @param {number} width - Width of the image in pixels
   * @param {number} height - Height of the image in pixels
   */

  function binaryToImage(array, width, height) {
    // Create the clamped data array
    var imageArray = new Uint8ClampedArray(array.buffer); // Create the image data

    var imageData = new ImageData(imageArray, width, height); // Create the canvas

    var canvas = document.createElement("canvas");
    var ctx = canvas.getContext("2d");
    canvas.width = imageData.width;
    canvas.height = imageData.height; // Draw the image

    ctx.putImageData(imageData, 0, 0); // Create the image, and grabe the URL of the canvas image

    var imageElem = new Image();
    imageElem.src = canvas.toDataURL();
    return imageElem;
  }

  var TGALoader = /*#__PURE__*/function (_DataTextureLoader) {
    _inherits(TGALoader, _DataTextureLoader);

    var _super = _createSuper(TGALoader);

    function TGALoader(manager) {
      _classCallCheck(this, TGALoader);

      return _super.call(this, manager);
    }

    _createClass(TGALoader, [{
      key: "parse",
      value: function parse(buffer) {
        // reference from vthibault, https://github.com/vthibault/roBrowser/blob/master/src/Loaders/Targa.js
        function tgaCheckHeader(header) {
          switch (header.image_type) {
            // check indexed type
            case TGA_TYPE_INDEXED:
            case TGA_TYPE_RLE_INDEXED:
              if (header.colormap_length > 256 || header.colormap_size !== 24 || header.colormap_type !== 1) {
                console.error("THREE.TGALoader: Invalid type colormap data for indexed type.");
              }

              break;
            // check colormap type

            case TGA_TYPE_RGB:
            case TGA_TYPE_GREY:
            case TGA_TYPE_RLE_RGB:
            case TGA_TYPE_RLE_GREY:
              if (header.colormap_type) {
                console.error("THREE.TGALoader: Invalid type colormap data for colormap type.");
              }

              break;
            // What the need of a file without data ?

            case TGA_TYPE_NO_DATA:
              console.error("THREE.TGALoader: No data.");
            // Invalid type ?

            default:
              console.error('THREE.TGALoader: Invalid type "%s".', header.image_type);
          } // check image width and height


          if (header.width <= 0 || header.height <= 0) {
            console.error("THREE.TGALoader: Invalid image size.");
          } // check image pixel size


          if (header.pixel_size !== 8 && header.pixel_size !== 16 && header.pixel_size !== 24 && header.pixel_size !== 32) {
            console.error('THREE.TGALoader: Invalid pixel size "%s".', header.pixel_size);
          }
        } // parse tga image buffer


        function tgaParse(use_rle, use_pal, header, offset, data) {
          var pixel_data, palettes;
          var pixel_size = header.pixel_size >> 3;
          var pixel_total = header.width * header.height * pixel_size; // read palettes

          if (use_pal) {
            palettes = data.subarray(offset, offset += header.colormap_length * (header.colormap_size >> 3));
          } // read RLE


          if (use_rle) {
            pixel_data = new Uint8Array(pixel_total);
            var c, count, i;
            var shift = 0;
            var pixels = new Uint8Array(pixel_size);

            while (shift < pixel_total) {
              c = data[offset++];
              count = (c & 0x7f) + 1; // RLE pixels

              if (c & 0x80) {
                // bind pixel tmp array
                for (i = 0; i < pixel_size; ++i) {
                  pixels[i] = data[offset++];
                } // copy pixel array


                for (i = 0; i < count; ++i) {
                  pixel_data.set(pixels, shift + i * pixel_size);
                }

                shift += pixel_size * count;
              } else {
                // raw pixels
                count *= pixel_size;

                for (i = 0; i < count; ++i) {
                  pixel_data[shift + i] = data[offset++];
                }

                shift += count;
              }
            }
          } else {
            // raw pixels
            pixel_data = data.subarray(offset, offset += use_pal ? header.width * header.height : pixel_total);
          }

          return {
            pixel_data: pixel_data,
            palettes: palettes
          };
        }

        function tgaGetImageData8bits(imageData, y_start, y_step, y_end, x_start, x_step, x_end, image, palettes) {
          var colormap = palettes;
          var color,
              i = 0,
              x,
              y;
          var width = header.width;

          for (y = y_start; y !== y_end; y += y_step) {
            for (x = x_start; x !== x_end; x += x_step, i++) {
              color = image[i];
              imageData[(x + width * y) * 4 + 3] = 255;
              imageData[(x + width * y) * 4 + 2] = colormap[color * 3 + 0];
              imageData[(x + width * y) * 4 + 1] = colormap[color * 3 + 1];
              imageData[(x + width * y) * 4 + 0] = colormap[color * 3 + 2];
            }
          }

          return imageData;
        }

        function tgaGetImageData16bits(imageData, y_start, y_step, y_end, x_start, x_step, x_end, image) {
          var color,
              i = 0,
              x,
              y;
          var width = header.width;

          for (y = y_start; y !== y_end; y += y_step) {
            for (x = x_start; x !== x_end; x += x_step, i += 2) {
              color = image[i + 0] + (image[i + 1] << 8);
              imageData[(x + width * y) * 4 + 0] = (color & 0x7c00) >> 7;
              imageData[(x + width * y) * 4 + 1] = (color & 0x03e0) >> 2;
              imageData[(x + width * y) * 4 + 2] = (color & 0x001f) << 3;
              imageData[(x + width * y) * 4 + 3] = color & 0x8000 ? 0 : 255;
            }
          }

          return imageData;
        }

        function tgaGetImageData24bits(imageData, y_start, y_step, y_end, x_start, x_step, x_end, image) {
          var i = 0,
              x,
              y;
          var width = header.width;

          for (y = y_start; y !== y_end; y += y_step) {
            for (x = x_start; x !== x_end; x += x_step, i += 3) {
              imageData[(x + width * y) * 4 + 3] = 255;
              imageData[(x + width * y) * 4 + 2] = image[i + 0];
              imageData[(x + width * y) * 4 + 1] = image[i + 1];
              imageData[(x + width * y) * 4 + 0] = image[i + 2];
            }
          }

          return imageData;
        }

        function tgaGetImageData32bits(imageData, y_start, y_step, y_end, x_start, x_step, x_end, image) {
          var i = 0,
              x,
              y;
          var width = header.width;

          for (y = y_start; y !== y_end; y += y_step) {
            for (x = x_start; x !== x_end; x += x_step, i += 4) {
              imageData[(x + width * y) * 4 + 2] = image[i + 0];
              imageData[(x + width * y) * 4 + 1] = image[i + 1];
              imageData[(x + width * y) * 4 + 0] = image[i + 2];
              imageData[(x + width * y) * 4 + 3] = image[i + 3];
            }
          }

          return imageData;
        }

        function tgaGetImageDataGrey8bits(imageData, y_start, y_step, y_end, x_start, x_step, x_end, image) {
          var color,
              i = 0,
              x,
              y;
          var width = header.width;

          for (y = y_start; y !== y_end; y += y_step) {
            for (x = x_start; x !== x_end; x += x_step, i++) {
              color = image[i];
              imageData[(x + width * y) * 4 + 0] = color;
              imageData[(x + width * y) * 4 + 1] = color;
              imageData[(x + width * y) * 4 + 2] = color;
              imageData[(x + width * y) * 4 + 3] = 255;
            }
          }

          return imageData;
        }

        function tgaGetImageDataGrey16bits(imageData, y_start, y_step, y_end, x_start, x_step, x_end, image) {
          var i = 0,
              x,
              y;
          var width = header.width;

          for (y = y_start; y !== y_end; y += y_step) {
            for (x = x_start; x !== x_end; x += x_step, i += 2) {
              imageData[(x + width * y) * 4 + 0] = image[i + 0];
              imageData[(x + width * y) * 4 + 1] = image[i + 0];
              imageData[(x + width * y) * 4 + 2] = image[i + 0];
              imageData[(x + width * y) * 4 + 3] = image[i + 1];
            }
          }

          return imageData;
        }

        function getTgaRGBA(data, width, height, image, palette) {
          var x_start, y_start, x_step, y_step, x_end, y_end;

          switch ((header.flags & TGA_ORIGIN_MASK) >> TGA_ORIGIN_SHIFT) {
            default:
            case TGA_ORIGIN_UL:
              x_start = 0;
              x_step = 1;
              x_end = width;
              y_start = 0;
              y_step = 1;
              y_end = height;
              break;

            case TGA_ORIGIN_BL:
              x_start = 0;
              x_step = 1;
              x_end = width;
              y_start = height - 1;
              y_step = -1;
              y_end = -1;
              break;

            case TGA_ORIGIN_UR:
              x_start = width - 1;
              x_step = -1;
              x_end = -1;
              y_start = 0;
              y_step = 1;
              y_end = height;
              break;

            case TGA_ORIGIN_BR:
              x_start = width - 1;
              x_step = -1;
              x_end = -1;
              y_start = height - 1;
              y_step = -1;
              y_end = -1;
              break;
          }

          if (use_grey) {
            switch (header.pixel_size) {
              case 8:
                tgaGetImageDataGrey8bits(data, y_start, y_step, y_end, x_start, x_step, x_end, image);
                break;

              case 16:
                tgaGetImageDataGrey16bits(data, y_start, y_step, y_end, x_start, x_step, x_end, image);
                break;

              default:
                console.error("THREE.TGALoader: Format not supported.");
                break;
            }
          } else {
            switch (header.pixel_size) {
              case 8:
                tgaGetImageData8bits(data, y_start, y_step, y_end, x_start, x_step, x_end, image, palette);
                break;

              case 16:
                tgaGetImageData16bits(data, y_start, y_step, y_end, x_start, x_step, x_end, image);
                break;

              case 24:
                tgaGetImageData24bits(data, y_start, y_step, y_end, x_start, x_step, x_end, image);
                break;

              case 32:
                tgaGetImageData32bits(data, y_start, y_step, y_end, x_start, x_step, x_end, image);
                break;

              default:
                console.error("THREE.TGALoader: Format not supported.");
                break;
            }
          } // Load image data according to specific method
          // let func = 'tgaGetImageData' + (use_grey ? 'Grey' : '') + (header.pixel_size) + 'bits';
          // func(data, y_start, y_step, y_end, x_start, x_step, x_end, width, image, palette );


          return data;
        } // TGA constants


        var TGA_TYPE_NO_DATA = 0,
            TGA_TYPE_INDEXED = 1,
            TGA_TYPE_RGB = 2,
            TGA_TYPE_GREY = 3,
            TGA_TYPE_RLE_INDEXED = 9,
            TGA_TYPE_RLE_RGB = 10,
            TGA_TYPE_RLE_GREY = 11,
            TGA_ORIGIN_MASK = 0x30,
            TGA_ORIGIN_SHIFT = 0x04,
            TGA_ORIGIN_BL = 0x00,
            TGA_ORIGIN_BR = 0x01,
            TGA_ORIGIN_UL = 0x02,
            TGA_ORIGIN_UR = 0x03;
        if (buffer.length < 19) console.error("THREE.TGALoader: Not enough data to contain header.");
        var offset = 0;
        var content = new Uint8Array(buffer),
            header = {
          id_length: content[offset++],
          colormap_type: content[offset++],
          image_type: content[offset++],
          colormap_index: content[offset++] | content[offset++] << 8,
          colormap_length: content[offset++] | content[offset++] << 8,
          colormap_size: content[offset++],
          origin: [content[offset++] | content[offset++] << 8, content[offset++] | content[offset++] << 8],
          width: content[offset++] | content[offset++] << 8,
          height: content[offset++] | content[offset++] << 8,
          pixel_size: content[offset++],
          flags: content[offset++]
        }; // check tga if it is valid format

        tgaCheckHeader(header);

        if (header.id_length + offset > buffer.length) {
          console.error("THREE.TGALoader: No data.");
        } // skip the needn't data


        offset += header.id_length; // get targa information about RLE compression and palette

        var use_rle = false,
            use_pal = false,
            use_grey = false;

        switch (header.image_type) {
          case TGA_TYPE_RLE_INDEXED:
            use_rle = true;
            use_pal = true;
            break;

          case TGA_TYPE_INDEXED:
            use_pal = true;
            break;

          case TGA_TYPE_RLE_RGB:
            use_rle = true;
            break;

          case TGA_TYPE_RGB:
            break;

          case TGA_TYPE_RLE_GREY:
            use_rle = true;
            use_grey = true;
            break;

          case TGA_TYPE_GREY:
            use_grey = true;
            break;
        } //


        var imageData = new Uint8Array(header.width * header.height * 4);
        var result = tgaParse(use_rle, use_pal, header, offset, content);
        getTgaRGBA(imageData, header.width, header.height, result.pixel_data, result.palettes);
        return {
          data: imageData,
          width: header.width,
          height: header.height,
          flipY: true,
          generateMipmaps: true,
          minFilter: THREE.LinearMipmapLinearFilter
        };
      }
    }]);

    return TGALoader;
  }(THREE.DataTextureLoader);

  /**
   * @author mrdoob / http://mrdoob.com/
   * @author Mugen87 / https://github.com/Mugen87
   *
   * Modified by German Mas:
   * - Restored the Up Axis rotation to its original state.
   * - Hardcode the up axis to always return Y_UP. This change was made in
   * previous versions of gzweb. Kept for backwards compatibility. If not used,
   * meshes that declare Z_UP have incorrect rotations, where we should have none.
   * The Y_UP prevents any further rotation from happening.
   * - getTexture had an sRGB encoding. Changed to Linear encoding to maintain the
   * behavior of previous versions.
   *
   * Diff of modification by Nate Koenig:
   *
  diff --git a/include/ColladaLoader.js b/include/ColladaLoader.js
  index cea5ac1..1980da1 100644
  --- a/include/ColladaLoader.js
  +++ b/include/ColladaLoader.js
  @@ -29,6 +29,7 @@ import {
      Quaternion,
      QuaternionKeyframeTrack,
      RepeatWrapping,
  +  RGBAFormat,
      Scene,
      Skeleton,
      SkinnedMesh,
  @@ -1644,14 +1645,14 @@ class ColladaLoader extends Loader {

                      if ( loader !== undefined ) {

  -						const texture = loader.load( image );
  +						let texture;

                          // Check against the cache, if enabled.
                          if (scope.enableTexturesCache && scope.texturesCache.has(image)) {
                              texture = scope.texturesCache.get(image);
                              return texture;
                          } else {
  -							savedPath = loader.path;
  +							const savedPath = loader.path;
                              // Remove the path if the image has a full URL.
                              if (image.startsWith('https://')) {
                                  loader.path = undefined;
  @@ -1689,7 +1690,7 @@ class ColladaLoader extends Loader {
                         imageElem.src = isJPEG ? "data:image/jpg;base64,": "data:image/png;base64,";
                         imageElem.src += window.btoa(binary);

  -                      scopeTexture.format = isJPEG ? THREE.RGBFormat : THREE.RGBAFormat;
  +                      scopeTexture.format = isJPEG ? RGBFormat : RGBAFormat;
                         scopeTexture.needsUpdate = true;
                         scopeTexture.image = imageElem;
                       });
  @@ -4216,9 +4217,9 @@ class ColladaLoader extends Loader {
          const scene = parseScene( getElementsByTagName( collada, 'scene' )[ 0 ] );
          scene.animations = animations;

  -		if ( asset.upAxis === 'Z_UP' ) {
  +		if ( asset.upAxis === 'Y_UP' ) {

  -			scene.quaternion.setFromEuler( new Euler( - Math.PI / 2, 0, 0 ) );
  +			scene.quaternion.setFromEuler( new Euler( Math.PI / 2, 0, 0 ) );

          }
   *
   *
   *
   * Modified by Nate Koenig :
   *
   *     Added a findResourceCb variable that is used by the texture loading
   *     in the `getTexture` function to fetch resources that were not
   *     accessible via standard URIs.
   *
   * Modified by German Mas:
   *
   * The Collada Loader caches the textures of meshes by default.
   * To disable:
   *   const loader = new THREE.ColladaLoader();
   *   loader.enableTexturesCache = false;
   *
   * Change the texture loader, if the requestHeader is present.
   * Texture Loaders use an Image Loader internally, instead of a File Loader.
   * Image Loader uses an img tag, and their src request doesn't accept custom headers.
   * See https://github.com/mrdoob/three.js/issues/10439
   *
   * Modified by Nate Koenig. Added the following to the 'parse' function:
   *
   * // A name or id could be a string enclosed by angle brackets like
   * // "<name>". A name like this will not be parsed correctly by the
   * // DOMParser, so we remove the angle brackets.
   * text = text.replace(/"\<(.*?)\>"/g, '"$1" ');
   * // Single quote version
   * text = text.replace(/'\<(.*?)\>'/g, '"$1" ');
   */

  var ColladaLoader = /*#__PURE__*/function (_Loader) {
    _inherits(ColladaLoader, _Loader);

    var _super = _createSuper(ColladaLoader);

    function ColladaLoader(manager) {
      var _this;

      _classCallCheck(this, ColladaLoader);

      _this = _super.call(this, manager); // Cache textures enabled by default.

      _this.enableTexturesCache = true; // The Map used to cache textures.

      _this.texturesCache = new Map();
      _this.findResourceCb = undefined;
      return _this;
    }

    _createClass(ColladaLoader, [{
      key: "load",
      value: function load(url, onLoad, onProgress, onError) {
        var scope = this;
        var path = scope.path === "" ? THREE.LoaderUtils.extractUrlBase(url) : scope.path;
        var loader = new THREE.FileLoader(scope.manager);
        loader.setPath(scope.path);
        loader.setRequestHeader(scope.requestHeader);
        loader.setWithCredentials(scope.withCredentials);
        loader.load(url, function (text) {
          try {
            onLoad(scope.parse(text, path));
          } catch (e) {
            if (onError) {
              onError(e);
            } else {
              console.error(e);
            }

            scope.manager.itemError(url);
          }
        }, onProgress, onError);
      }
    }, {
      key: "parse",
      value: function parse(text, path) {
        function getElementsByTagName(xml, name) {
          // Non recursive xml.getElementsByTagName() ...
          var array = [];
          var childNodes = xml.childNodes;

          for (var i = 0, l = childNodes.length; i < l; i++) {
            var child = childNodes[i];

            if (child.nodeName === name) {
              array.push(child);
            }
          }

          return array;
        }

        function parseStrings(text) {
          if (text.length === 0) return [];
          var parts = text.trim().split(/\s+/);
          var array = new Array(parts.length);

          for (var i = 0, l = parts.length; i < l; i++) {
            array[i] = parts[i];
          }

          return array;
        }

        function parseFloats(text) {
          if (text.length === 0) return [];
          var parts = text.trim().split(/\s+/);
          var array = new Array(parts.length);

          for (var i = 0, l = parts.length; i < l; i++) {
            array[i] = parseFloat(parts[i]);
          }

          return array;
        }

        function parseInts(text) {
          if (text.length === 0) return [];
          var parts = text.trim().split(/\s+/);
          var array = new Array(parts.length);

          for (var i = 0, l = parts.length; i < l; i++) {
            array[i] = parseInt(parts[i]);
          }

          return array;
        }

        function parseId(text) {
          return text.substring(1);
        }

        function generateId() {
          return "three_default_" + count++;
        }

        function isEmpty(object) {
          return Object.keys(object).length === 0;
        } // asset


        function parseAsset(xml) {
          return {
            unit: parseAssetUnit(getElementsByTagName(xml, "unit")[0]),
            upAxis: parseAssetUpAxis(getElementsByTagName(xml, "up_axis")[0])
          };
        }

        function parseAssetUnit(xml) {
          if (xml !== undefined && xml.hasAttribute("meter") === true) {
            return parseFloat(xml.getAttribute("meter"));
          } else {
            return 1; // default 1 meter
          }
        }

        function parseAssetUpAxis(xml) {
          // Modified by German Mas.
          // Hardcode Y_UP in order to prevent unnecesary rotations on meshes.
          return "Y_UP";
        } // library


        function parseLibrary(xml, libraryName, nodeName, parser) {
          var library = getElementsByTagName(xml, libraryName)[0];

          if (library !== undefined) {
            var elements = getElementsByTagName(library, nodeName);

            for (var i = 0; i < elements.length; i++) {
              parser(elements[i]);
            }
          }
        }

        function buildLibrary(data, builder) {
          for (var name in data) {
            var object = data[name];
            object.build = builder(data[name]);
          }
        } // get


        function getBuild(data, builder) {
          if (data.build !== undefined) return data.build;
          data.build = builder(data);
          return data.build;
        } // animation


        function parseAnimation(xml) {
          var data = {
            sources: {},
            samplers: {},
            channels: {}
          };
          var hasChildren = false;

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;
            var id = void 0;

            switch (child.nodeName) {
              case "source":
                id = child.getAttribute("id");
                data.sources[id] = parseSource(child);
                break;

              case "sampler":
                id = child.getAttribute("id");
                data.samplers[id] = parseAnimationSampler(child);
                break;

              case "channel":
                id = child.getAttribute("target");
                data.channels[id] = parseAnimationChannel(child);
                break;

              case "animation":
                // hierarchy of related animations
                parseAnimation(child);
                hasChildren = true;
                break;

              default:
                console.log(child);
            }
          }

          if (hasChildren === false) {
            // since 'id' attributes can be optional, it's necessary to generate a UUID for unqiue assignment
            library.animations[xml.getAttribute("id") || THREE.MathUtils.generateUUID()] = data;
          }
        }

        function parseAnimationSampler(xml) {
          var data = {
            inputs: {}
          };

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "input":
                var id = parseId(child.getAttribute("source"));
                var semantic = child.getAttribute("semantic");
                data.inputs[semantic] = id;
                break;
            }
          }

          return data;
        }

        function parseAnimationChannel(xml) {
          var data = {};
          var target = xml.getAttribute("target"); // parsing SID Addressing Syntax

          var parts = target.split("/");
          var id = parts.shift();
          var sid = parts.shift(); // check selection syntax

          var arraySyntax = sid.indexOf("(") !== -1;
          var memberSyntax = sid.indexOf(".") !== -1;

          if (memberSyntax) {
            //  member selection access
            parts = sid.split(".");
            sid = parts.shift();
            data.member = parts.shift();
          } else if (arraySyntax) {
            // array-access syntax. can be used to express fields in one-dimensional vectors or two-dimensional matrices.
            var indices = sid.split("(");
            sid = indices.shift();

            for (var i = 0; i < indices.length; i++) {
              indices[i] = parseInt(indices[i].replace(/\)/, ""));
            }

            data.indices = indices;
          }

          data.id = id;
          data.sid = sid;
          data.arraySyntax = arraySyntax;
          data.memberSyntax = memberSyntax;
          data.sampler = parseId(xml.getAttribute("source"));
          return data;
        }

        function buildAnimation(data) {
          var tracks = [];
          var channels = data.channels;
          var samplers = data.samplers;
          var sources = data.sources;

          for (var target in channels) {
            if (channels.hasOwnProperty(target)) {
              var channel = channels[target];
              var sampler = samplers[channel.sampler];
              var inputId = sampler.inputs.INPUT;
              var outputId = sampler.inputs.OUTPUT;
              var inputSource = sources[inputId];
              var outputSource = sources[outputId];
              var animation = buildAnimationChannel(channel, inputSource, outputSource);
              createKeyframeTracks(animation, tracks);
            }
          }

          return tracks;
        }

        function getAnimation(id) {
          return getBuild(library.animations[id], buildAnimation);
        }

        function buildAnimationChannel(channel, inputSource, outputSource) {
          var node = library.nodes[channel.id];
          var object3D = getNode(node.id);
          var transform = node.transforms[channel.sid];
          var defaultMatrix = node.matrix.clone().transpose();
          var time, stride;
          var i, il, j, jl;
          var data = {}; // the collada spec allows the animation of data in various ways.
          // depending on the transform type (matrix, translate, rotate, scale), we execute different logic

          switch (transform) {
            case "matrix":
              for (i = 0, il = inputSource.array.length; i < il; i++) {
                time = inputSource.array[i];
                stride = i * outputSource.stride;
                if (data[time] === undefined) data[time] = {};

                if (channel.arraySyntax === true) {
                  var value = outputSource.array[stride];
                  var index = channel.indices[0] + 4 * channel.indices[1];
                  data[time][index] = value;
                } else {
                  for (j = 0, jl = outputSource.stride; j < jl; j++) {
                    data[time][j] = outputSource.array[stride + j];
                  }
                }
              }

              break;

            case "translate":
              console.warn('THREE.ColladaLoader: Animation transform type "%s" not yet implemented.', transform);
              break;

            case "rotate":
              console.warn('THREE.ColladaLoader: Animation transform type "%s" not yet implemented.', transform);
              break;

            case "scale":
              console.warn('THREE.ColladaLoader: Animation transform type "%s" not yet implemented.', transform);
              break;
          }

          var keyframes = prepareAnimationData(data, defaultMatrix);
          var animation = {
            name: object3D.uuid,
            keyframes: keyframes
          };
          return animation;
        }

        function prepareAnimationData(data, defaultMatrix) {
          var keyframes = []; // transfer data into a sortable array

          for (var time in data) {
            keyframes.push({
              time: parseFloat(time),
              value: data[time]
            });
          } // ensure keyframes are sorted by time


          keyframes.sort(ascending); // now we clean up all animation data, so we can use them for keyframe tracks

          for (var i = 0; i < 16; i++) {
            transformAnimationData(keyframes, i, defaultMatrix.elements[i]);
          }

          return keyframes; // array sort function

          function ascending(a, b) {
            return a.time - b.time;
          }
        }

        var position = new THREE.Vector3();
        var scale = new THREE.Vector3();
        var quaternion = new THREE.Quaternion();

        function createKeyframeTracks(animation, tracks) {
          var keyframes = animation.keyframes;
          var name = animation.name;
          var times = [];
          var positionData = [];
          var quaternionData = [];
          var scaleData = [];

          for (var i = 0, l = keyframes.length; i < l; i++) {
            var keyframe = keyframes[i];
            var time = keyframe.time;
            var value = keyframe.value;
            matrix.fromArray(value).transpose();
            matrix.decompose(position, quaternion, scale);
            times.push(time);
            positionData.push(position.x, position.y, position.z);
            quaternionData.push(quaternion.x, quaternion.y, quaternion.z, quaternion.w);
            scaleData.push(scale.x, scale.y, scale.z);
          }

          if (positionData.length > 0) tracks.push(new THREE.VectorKeyframeTrack(name + ".position", times, positionData));
          if (quaternionData.length > 0) tracks.push(new THREE.QuaternionKeyframeTrack(name + ".quaternion", times, quaternionData));
          if (scaleData.length > 0) tracks.push(new THREE.VectorKeyframeTrack(name + ".scale", times, scaleData));
          return tracks;
        }

        function transformAnimationData(keyframes, property, defaultValue) {
          var keyframe;
          var empty = true;
          var i, l; // check, if values of a property are missing in our keyframes

          for (i = 0, l = keyframes.length; i < l; i++) {
            keyframe = keyframes[i];

            if (keyframe.value[property] === undefined) {
              keyframe.value[property] = null; // mark as missing
            } else {
              empty = false;
            }
          }

          if (empty === true) {
            // no values at all, so we set a default value
            for (i = 0, l = keyframes.length; i < l; i++) {
              keyframe = keyframes[i];
              keyframe.value[property] = defaultValue;
            }
          } else {
            // filling gaps
            createMissingKeyframes(keyframes, property);
          }
        }

        function createMissingKeyframes(keyframes, property) {
          var prev, next;

          for (var i = 0, l = keyframes.length; i < l; i++) {
            var keyframe = keyframes[i];

            if (keyframe.value[property] === null) {
              prev = getPrev(keyframes, i, property);
              next = getNext(keyframes, i, property);

              if (prev === null) {
                keyframe.value[property] = next.value[property];
                continue;
              }

              if (next === null) {
                keyframe.value[property] = prev.value[property];
                continue;
              }

              interpolate(keyframe, prev, next, property);
            }
          }
        }

        function getPrev(keyframes, i, property) {
          while (i >= 0) {
            var keyframe = keyframes[i];
            if (keyframe.value[property] !== null) return keyframe;
            i--;
          }

          return null;
        }

        function getNext(keyframes, i, property) {
          while (i < keyframes.length) {
            var keyframe = keyframes[i];
            if (keyframe.value[property] !== null) return keyframe;
            i++;
          }

          return null;
        }

        function interpolate(key, prev, next, property) {
          if (next.time - prev.time === 0) {
            key.value[property] = prev.value[property];
            return;
          }

          key.value[property] = (key.time - prev.time) * (next.value[property] - prev.value[property]) / (next.time - prev.time) + prev.value[property];
        } // animation clips


        function parseAnimationClip(xml) {
          var data = {
            name: xml.getAttribute("id") || "default",
            start: parseFloat(xml.getAttribute("start") || 0),
            end: parseFloat(xml.getAttribute("end") || 0),
            animations: []
          };

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "instance_animation":
                data.animations.push(parseId(child.getAttribute("url")));
                break;
            }
          }

          library.clips[xml.getAttribute("id")] = data;
        }

        function buildAnimationClip(data) {
          var tracks = [];
          var name = data.name;
          var duration = data.end - data.start || -1;
          var animations = data.animations;

          for (var i = 0, il = animations.length; i < il; i++) {
            var animationTracks = getAnimation(animations[i]);

            for (var j = 0, jl = animationTracks.length; j < jl; j++) {
              tracks.push(animationTracks[j]);
            }
          }

          return new THREE.AnimationClip(name, duration, tracks);
        }

        function getAnimationClip(id) {
          return getBuild(library.clips[id], buildAnimationClip);
        } // controller


        function parseController(xml) {
          var data = {};

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "skin":
                // there is exactly one skin per controller
                data.id = parseId(child.getAttribute("source"));
                data.skin = parseSkin(child);
                break;

              case "morph":
                data.id = parseId(child.getAttribute("source"));
                console.warn("THREE.ColladaLoader: Morph target animation not supported yet.");
                break;
            }
          }

          library.controllers[xml.getAttribute("id")] = data;
        }

        function parseSkin(xml) {
          var data = {
            sources: {}
          };

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "bind_shape_matrix":
                data.bindShapeMatrix = parseFloats(child.textContent);
                break;

              case "source":
                var id = child.getAttribute("id");
                data.sources[id] = parseSource(child);
                break;

              case "joints":
                data.joints = parseJoints(child);
                break;

              case "vertex_weights":
                data.vertexWeights = parseVertexWeights(child);
                break;
            }
          }

          return data;
        }

        function parseJoints(xml) {
          var data = {
            inputs: {}
          };

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "input":
                var semantic = child.getAttribute("semantic");
                var id = parseId(child.getAttribute("source"));
                data.inputs[semantic] = id;
                break;
            }
          }

          return data;
        }

        function parseVertexWeights(xml) {
          var data = {
            inputs: {}
          };

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "input":
                var semantic = child.getAttribute("semantic");
                var id = parseId(child.getAttribute("source"));
                var offset = parseInt(child.getAttribute("offset"));
                data.inputs[semantic] = {
                  id: id,
                  offset: offset
                };
                break;

              case "vcount":
                data.vcount = parseInts(child.textContent);
                break;

              case "v":
                data.v = parseInts(child.textContent);
                break;
            }
          }

          return data;
        }

        function buildController(data) {
          var build = {
            id: data.id
          };
          var geometry = library.geometries[build.id];

          if (data.skin !== undefined) {
            build.skin = buildSkin(data.skin); // we enhance the 'sources' property of the corresponding geometry with our skin data

            geometry.sources.skinIndices = build.skin.indices;
            geometry.sources.skinWeights = build.skin.weights;
          }

          return build;
        }

        function buildSkin(data) {
          var BONE_LIMIT = 4;
          var build = {
            joints: [],
            indices: {
              array: [],
              stride: BONE_LIMIT
            },
            weights: {
              array: [],
              stride: BONE_LIMIT
            }
          };
          var sources = data.sources;
          var vertexWeights = data.vertexWeights;
          var vcount = vertexWeights.vcount;
          var v = vertexWeights.v;
          var jointOffset = vertexWeights.inputs.JOINT.offset;
          var weightOffset = vertexWeights.inputs.WEIGHT.offset;
          var jointSource = data.sources[data.joints.inputs.JOINT];
          var inverseSource = data.sources[data.joints.inputs.INV_BIND_MATRIX];
          var weights = sources[vertexWeights.inputs.WEIGHT.id].array;
          var stride = 0;
          var i, j, l; // procces skin data for each vertex

          for (i = 0, l = vcount.length; i < l; i++) {
            var jointCount = vcount[i]; // this is the amount of joints that affect a single vertex

            var vertexSkinData = [];

            for (j = 0; j < jointCount; j++) {
              var skinIndex = v[stride + jointOffset];
              var weightId = v[stride + weightOffset];
              var skinWeight = weights[weightId];
              vertexSkinData.push({
                index: skinIndex,
                weight: skinWeight
              });
              stride += 2;
            } // we sort the joints in descending order based on the weights.
            // this ensures, we only procced the most important joints of the vertex


            vertexSkinData.sort(descending); // now we provide for each vertex a set of four index and weight values.
            // the order of the skin data matches the order of vertices

            for (j = 0; j < BONE_LIMIT; j++) {
              var d = vertexSkinData[j];

              if (d !== undefined) {
                build.indices.array.push(d.index);
                build.weights.array.push(d.weight);
              } else {
                build.indices.array.push(0);
                build.weights.array.push(0);
              }
            }
          } // setup bind matrix


          if (data.bindShapeMatrix) {
            build.bindMatrix = new THREE.Matrix4().fromArray(data.bindShapeMatrix).transpose();
          } else {
            build.bindMatrix = new THREE.Matrix4().identity();
          } // process bones and inverse bind matrix data


          for (i = 0, l = jointSource.array.length; i < l; i++) {
            var name = jointSource.array[i];
            var boneInverse = new THREE.Matrix4().fromArray(inverseSource.array, i * inverseSource.stride).transpose();
            build.joints.push({
              name: name,
              boneInverse: boneInverse
            });
          }

          return build; // array sort function

          function descending(a, b) {
            return b.weight - a.weight;
          }
        }

        function getController(id) {
          return getBuild(library.controllers[id], buildController);
        } // image


        function parseImage(xml) {
          var data = {
            init_from: getElementsByTagName(xml, "init_from")[0].textContent
          };
          library.images[xml.getAttribute("id")] = data;
        }

        function buildImage(data) {
          if (data.build !== undefined) return data.build;
          return data.init_from;
        }

        function getImage(id) {
          var data = library.images[id];

          if (data !== undefined) {
            return getBuild(data, buildImage);
          }

          console.warn("THREE.ColladaLoader: Couldn't find image with ID:", id);
          return null;
        } // effect


        function parseEffect(xml) {
          var data = {};

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "profile_COMMON":
                data.profile = parseEffectProfileCOMMON(child);
                break;
            }
          }

          library.effects[xml.getAttribute("id")] = data;
        }

        function parseEffectProfileCOMMON(xml) {
          var data = {
            surfaces: {},
            samplers: {}
          };

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "newparam":
                parseEffectNewparam(child, data);
                break;

              case "technique":
                data.technique = parseEffectTechnique(child);
                break;

              case "extra":
                data.extra = parseEffectExtra(child);
                break;
            }
          }

          return data;
        }

        function parseEffectNewparam(xml, data) {
          var sid = xml.getAttribute("sid");

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "surface":
                data.surfaces[sid] = parseEffectSurface(child);
                break;

              case "sampler2D":
                data.samplers[sid] = parseEffectSampler(child);
                break;
            }
          }
        }

        function parseEffectSurface(xml) {
          var data = {};

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "init_from":
                data.init_from = child.textContent;
                break;
            }
          }

          return data;
        }

        function parseEffectSampler(xml) {
          var data = {};

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "source":
                data.source = child.textContent;
                break;
            }
          }

          return data;
        }

        function parseEffectTechnique(xml) {
          var data = {};

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "constant":
              case "lambert":
              case "blinn":
              case "phong":
                data.type = child.nodeName;
                data.parameters = parseEffectParameters(child);
                break;

              case "extra":
                data.extra = parseEffectExtra(child);
                break;
            }
          }

          return data;
        }

        function parseEffectParameters(xml) {
          var data = {};

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "emission":
              case "diffuse":
              case "specular":
              case "bump":
              case "ambient":
              case "shininess":
              case "transparency":
                data[child.nodeName] = parseEffectParameter(child);
                break;

              case "transparent":
                data[child.nodeName] = {
                  opaque: child.hasAttribute("opaque") ? child.getAttribute("opaque") : "A_ONE",
                  data: parseEffectParameter(child)
                };
                break;
            }
          }

          return data;
        }

        function parseEffectParameter(xml) {
          var data = {};

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "color":
                data[child.nodeName] = parseFloats(child.textContent);
                break;

              case "float":
                data[child.nodeName] = parseFloat(child.textContent);
                break;

              case "texture":
                data[child.nodeName] = {
                  id: child.getAttribute("texture"),
                  extra: parseEffectParameterTexture(child)
                };
                break;
            }
          }

          return data;
        }

        function parseEffectParameterTexture(xml) {
          var data = {
            technique: {}
          };

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "extra":
                parseEffectParameterTextureExtra(child, data);
                break;
            }
          }

          return data;
        }

        function parseEffectParameterTextureExtra(xml, data) {
          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "technique":
                parseEffectParameterTextureExtraTechnique(child, data);
                break;
            }
          }
        }

        function parseEffectParameterTextureExtraTechnique(xml, data) {
          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "repeatU":
              case "repeatV":
              case "offsetU":
              case "offsetV":
                data.technique[child.nodeName] = parseFloat(child.textContent);
                break;

              case "wrapU":
              case "wrapV":
                // some files have values for wrapU/wrapV which become NaN via parseInt
                if (child.textContent.toUpperCase() === "TRUE") {
                  data.technique[child.nodeName] = 1;
                } else if (child.textContent.toUpperCase() === "FALSE") {
                  data.technique[child.nodeName] = 0;
                } else {
                  data.technique[child.nodeName] = parseInt(child.textContent);
                }

                break;

              case "bump":
                data[child.nodeName] = parseEffectExtraTechniqueBump(child);
                break;
            }
          }
        }

        function parseEffectExtra(xml) {
          var data = {};

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "technique":
                data.technique = parseEffectExtraTechnique(child);
                break;
            }
          }

          return data;
        }

        function parseEffectExtraTechnique(xml) {
          var data = {};

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "double_sided":
                data[child.nodeName] = parseInt(child.textContent);
                break;

              case "bump":
                data[child.nodeName] = parseEffectExtraTechniqueBump(child);
                break;
            }
          }

          return data;
        }

        function parseEffectExtraTechniqueBump(xml) {
          var data = {};

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "texture":
                data[child.nodeName] = {
                  id: child.getAttribute("texture"),
                  texcoord: child.getAttribute("texcoord"),
                  extra: parseEffectParameterTexture(child)
                };
                break;
            }
          }

          return data;
        }

        function buildEffect(data) {
          return data;
        }

        function getEffect(id) {
          return getBuild(library.effects[id], buildEffect);
        } // material


        function parseMaterial(xml) {
          var data = {
            name: xml.getAttribute("name")
          };

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "instance_effect":
                data.url = parseId(child.getAttribute("url"));
                break;
            }
          }

          library.materials[xml.getAttribute("id")] = data;
        }

        function getTextureLoader(image) {
          var loader;
          var extension = image.slice((image.lastIndexOf(".") - 1 >>> 0) + 2); // http://www.jstips.co/en/javascript/get-file-extension/

          extension = extension.toLowerCase();

          switch (extension) {
            case "tga":
              loader = tgaLoader;
              break;

            default:
              loader = textureLoader;
          }

          return loader;
        }

        function buildMaterial(data) {
          var effect = getEffect(data.url);
          var technique = effect.profile.technique;
          var material;

          switch (technique.type) {
            case "phong":
            case "blinn":
              material = new THREE.MeshPhongMaterial();
              break;

            case "lambert":
              material = new THREE.MeshLambertMaterial();
              break;

            default:
              material = new THREE.MeshBasicMaterial();
              break;
          }

          material.name = data.name || "";

          function getTexture(textureObject) {
            var encoding = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : null;
            var sampler = effect.profile.samplers[textureObject.id];
            var image = null; // get image

            if (sampler !== undefined) {
              var surface = effect.profile.surfaces[sampler.source];
              image = getImage(surface.init_from);
            } else {
              console.warn("THREE.ColladaLoader: Undefined sampler. Access image directly (see #12530).");
              image = getImage(textureObject.id);
            } // create texture if image is avaiable


            if (image !== null) {
              var loader = getTextureLoader(image);

              if (loader !== undefined) {
                var texture; // Check against the cache, if enabled.

                if (scope.enableTexturesCache && scope.texturesCache.has(image)) {
                  texture = scope.texturesCache.get(image);
                  return texture;
                } else {
                  var savedPath = loader.path; // Remove the path if the image has a full URL.

                  if (image.startsWith("https://")) {
                    loader.path = undefined;
                  }

                  texture = loader.load(image, // onLoad
                  undefined, // onProgress
                  undefined, // onError
                  function (error) {
                    if (scope.findResourceCb) {
                      // Create the filename to look up.
                      var filename = [path.substring(0, path.lastIndexOf("/")), image].join("/"); // Store the texture pointer

                      var scopeTexture = texture; // Get the image using the find resource callback.

                      scope.findResourceCb(filename, function (imageBytes, error) {
                        var item = "".concat(savedPath).concat(image);

                        if (error !== undefined) {
                          // Mark the texture as error in the loading manager.
                          loader.manager.markAsError(item);
                          return;
                        } // Create the image element


                        var imageElem = document.createElementNS("http://www.w3.org/1999/xhtml", "img");
                        var isJPEG = filename.search(/\.jpe?g($|\?)/i) > 0 || filename.search(/^data\:image\/jpeg/) === 0;
                        var binary = "";
                        var len = imageBytes.byteLength;

                        for (var i = 0; i < len; i++) {
                          binary += String.fromCharCode(imageBytes[i]);
                        } // Set the image source using base64 encoding


                        imageElem.src = isJPEG ? "data:image/jpg;base64," : "data:image/png;base64,";
                        imageElem.src += window.btoa(binary);
                        scopeTexture.format = isJPEG ? RGBFormat : THREE.RGBAFormat;
                        scopeTexture.needsUpdate = true;
                        scopeTexture.image = imageElem; // Mark the texture as done in the loading manager.

                        loader.manager.markAsDone(item);
                      });
                    }
                  }); // Restore the path.

                  loader.path = savedPath;
                }

                var extra = textureObject.extra;

                if (extra !== undefined && extra.technique !== undefined && isEmpty(extra.technique) === false) {
                  var _technique = extra.technique;
                  texture.wrapS = _technique.wrapU ? THREE.RepeatWrapping : THREE.ClampToEdgeWrapping;
                  texture.wrapT = _technique.wrapV ? THREE.RepeatWrapping : THREE.ClampToEdgeWrapping;
                  texture.offset.set(_technique.offsetU || 0, _technique.offsetV || 0);
                  texture.repeat.set(_technique.repeatU || 1, _technique.repeatV || 1);
                } else {
                  texture.wrapS = THREE.RepeatWrapping;
                  texture.wrapT = THREE.RepeatWrapping;
                }

                if (encoding !== null) {
                  texture.encoding = encoding;
                } // Add the texture to the Cache map, if enabled.


                if (scope.enableTexturesCache) {
                  scope.texturesCache.set(image, texture);
                }

                return texture;
              } else {
                console.warn("THREE.ColladaLoader: Loader for texture %s not found.", image);
                return null;
              }
            } else {
              console.warn("THREE.ColladaLoader: Couldn't create texture with ID:", textureObject.id);
              return null;
            }
          }

          var parameters = technique.parameters;

          for (var key in parameters) {
            var parameter = parameters[key];

            switch (key) {
              case "diffuse":
                if (parameter.color) material.color.fromArray(parameter.color);
                if (parameter.texture) material.map = getTexture(parameter.texture, THREE.LinearEncoding);
                break;

              case "specular":
                if (parameter.color && material.specular) material.specular.fromArray(parameter.color);
                if (parameter.texture) material.specularMap = getTexture(parameter.texture);
                break;

              case "bump":
                if (parameter.texture) material.normalMap = getTexture(parameter.texture);
                break;

              case "ambient":
                if (parameter.texture) material.lightMap = getTexture(parameter.texture, THREE.LinearEncoding);
                break;

              case "shininess":
                if (parameter["float"] && material.shininess) material.shininess = parameter["float"];
                break;

              case "emission":
                if (parameter.color && material.emissive) material.emissive.fromArray(parameter.color);
                if (parameter.texture) material.emissiveMap = getTexture(parameter.texture, THREE.LinearEncoding);
                break;
            }
          } // Modified by German Mas.
          // getTexture already uses Linear encoding. No need to convert.
          // material.color.convertSRGBToLinear();
          // if ( material.specular ) material.specular.convertSRGBToLinear();
          // if ( material.emissive ) material.emissive.convertSRGBToLinear();
          //


          var transparent = parameters["transparent"];
          var transparency = parameters["transparency"]; // <transparency> does not exist but <transparent>

          if (transparency === undefined && transparent) {
            transparency = {
              "float": 1
            };
          } // <transparent> does not exist but <transparency>


          if (transparent === undefined && transparency) {
            transparent = {
              opaque: "A_ONE",
              data: {
                color: [1, 1, 1, 1]
              }
            };
          }

          if (transparent && transparency) {
            // handle case if a texture exists but no color
            if (transparent.data.texture) {
              // we do not set an alpha map (see #13792)
              material.transparent = true;
            } else {
              var color = transparent.data.color;

              switch (transparent.opaque) {
                case "A_ONE":
                  material.opacity = color[3] * transparency["float"];
                  break;

                case "RGB_ZERO":
                  material.opacity = 1 - color[0] * transparency["float"];
                  break;

                case "A_ZERO":
                  material.opacity = 1 - color[3] * transparency["float"];
                  break;

                case "RGB_ONE":
                  material.opacity = color[0] * transparency["float"];
                  break;

                default:
                  console.warn('THREE.ColladaLoader: Invalid opaque type "%s" of transparent tag.', transparent.opaque);
              }

              if (material.opacity < 1) material.transparent = true;
            }
          } //


          if (technique.extra !== undefined && technique.extra.technique !== undefined) {
            var techniques = technique.extra.technique;

            for (var k in techniques) {
              var v = techniques[k];

              switch (k) {
                case "double_sided":
                  material.side = v === 1 ? THREE.DoubleSide : THREE.FrontSide;
                  break;

                case "bump":
                  material.normalMap = getTexture(v.texture);
                  material.normalScale = new THREE.Vector2(1, 1);
                  break;
              }
            }
          }

          return material;
        }

        function getMaterial(id) {
          return getBuild(library.materials[id], buildMaterial);
        } // camera


        function parseCamera(xml) {
          var data = {
            name: xml.getAttribute("name")
          };

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "optics":
                data.optics = parseCameraOptics(child);
                break;
            }
          }

          library.cameras[xml.getAttribute("id")] = data;
        }

        function parseCameraOptics(xml) {
          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];

            switch (child.nodeName) {
              case "technique_common":
                return parseCameraTechnique(child);
            }
          }

          return {};
        }

        function parseCameraTechnique(xml) {
          var data = {};

          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];

            switch (child.nodeName) {
              case "perspective":
              case "orthographic":
                data.technique = child.nodeName;
                data.parameters = parseCameraParameters(child);
                break;
            }
          }

          return data;
        }

        function parseCameraParameters(xml) {
          var data = {};

          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];

            switch (child.nodeName) {
              case "xfov":
              case "yfov":
              case "xmag":
              case "ymag":
              case "znear":
              case "zfar":
              case "aspect_ratio":
                data[child.nodeName] = parseFloat(child.textContent);
                break;
            }
          }

          return data;
        }

        function buildCamera(data) {
          var camera;

          switch (data.optics.technique) {
            case "perspective":
              camera = new THREE.PerspectiveCamera(data.optics.parameters.yfov, data.optics.parameters.aspect_ratio, data.optics.parameters.znear, data.optics.parameters.zfar);
              break;

            case "orthographic":
              var ymag = data.optics.parameters.ymag;
              var xmag = data.optics.parameters.xmag;
              var aspectRatio = data.optics.parameters.aspect_ratio;
              xmag = xmag === undefined ? ymag * aspectRatio : xmag;
              ymag = ymag === undefined ? xmag / aspectRatio : ymag;
              xmag *= 0.5;
              ymag *= 0.5;
              camera = new THREE.OrthographicCamera(-xmag, xmag, ymag, -ymag, // left, right, top, bottom
              data.optics.parameters.znear, data.optics.parameters.zfar);
              break;

            default:
              camera = new THREE.PerspectiveCamera();
              break;
          }

          camera.name = data.name || "";
          return camera;
        }

        function getCamera(id) {
          var data = library.cameras[id];

          if (data !== undefined) {
            return getBuild(data, buildCamera);
          }

          console.warn("THREE.ColladaLoader: Couldn't find camera with ID:", id);
          return null;
        } // light


        function parseLight(xml) {
          var data = {};

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "technique_common":
                data = parseLightTechnique(child);
                break;
            }
          }

          library.lights[xml.getAttribute("id")] = data;
        }

        function parseLightTechnique(xml) {
          var data = {};

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "directional":
              case "point":
              case "spot":
              case "ambient":
                data.technique = child.nodeName;
                data.parameters = parseLightParameters(child);
            }
          }

          return data;
        }

        function parseLightParameters(xml) {
          var data = {};

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "color":
                var array = parseFloats(child.textContent);
                data.color = new THREE.Color().fromArray(array).convertSRGBToLinear();
                break;

              case "falloff_angle":
                data.falloffAngle = parseFloat(child.textContent);
                break;

              case "quadratic_attenuation":
                var f = parseFloat(child.textContent);
                data.distance = f ? Math.sqrt(1 / f) : 0;
                break;
            }
          }

          return data;
        }

        function buildLight(data) {
          var light;

          switch (data.technique) {
            case "directional":
              light = new THREE.DirectionalLight();
              break;

            case "point":
              light = new THREE.PointLight();
              break;

            case "spot":
              light = new THREE.SpotLight();
              break;

            case "ambient":
              light = new THREE.AmbientLight();
              break;
          }

          if (data.parameters.color) light.color.copy(data.parameters.color);
          if (data.parameters.distance) light.distance = data.parameters.distance;
          return light;
        }

        function getLight(id) {
          var data = library.lights[id];

          if (data !== undefined) {
            return getBuild(data, buildLight);
          }

          console.warn("THREE.ColladaLoader: Couldn't find light with ID:", id);
          return null;
        } // geometry


        function parseGeometry(xml) {
          var data = {
            name: xml.getAttribute("name"),
            sources: {},
            vertices: {},
            primitives: []
          };
          var mesh = getElementsByTagName(xml, "mesh")[0]; // the following tags inside geometry are not supported yet (see https://github.com/mrdoob/three.js/pull/12606): convex_mesh, spline, brep

          if (mesh === undefined) return;

          for (var i = 0; i < mesh.childNodes.length; i++) {
            var child = mesh.childNodes[i];
            if (child.nodeType !== 1) continue;
            var id = child.getAttribute("id");

            switch (child.nodeName) {
              case "source":
                data.sources[id] = parseSource(child);
                break;

              case "vertices":
                // data.sources[ id ] = data.sources[ parseId( getElementsByTagName( child, 'input' )[ 0 ].getAttribute( 'source' ) ) ];
                data.vertices = parseGeometryVertices(child);
                break;

              case "polygons":
                console.warn("THREE.ColladaLoader: Unsupported primitive type: ", child.nodeName);
                break;

              case "lines":
              case "linestrips":
              case "polylist":
              case "triangles":
                data.primitives.push(parseGeometryPrimitive(child));
                break;

              default:
                console.log(child);
            }
          }

          library.geometries[xml.getAttribute("id")] = data;
        }

        function parseSource(xml) {
          var data = {
            array: [],
            stride: 3
          };

          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "float_array":
                data.array = parseFloats(child.textContent);
                break;

              case "Name_array":
                data.array = parseStrings(child.textContent);
                break;

              case "technique_common":
                var accessor = getElementsByTagName(child, "accessor")[0];

                if (accessor !== undefined) {
                  data.stride = parseInt(accessor.getAttribute("stride"));
                }

                break;
            }
          }

          return data;
        }

        function parseGeometryVertices(xml) {
          var data = {};

          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;
            data[child.getAttribute("semantic")] = parseId(child.getAttribute("source"));
          }

          return data;
        }

        function parseGeometryPrimitive(xml) {
          var primitive = {
            type: xml.nodeName,
            material: xml.getAttribute("material"),
            count: parseInt(xml.getAttribute("count")),
            inputs: {},
            stride: 0,
            hasUV: false
          };

          for (var i = 0, l = xml.childNodes.length; i < l; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "input":
                var id = parseId(child.getAttribute("source"));
                var semantic = child.getAttribute("semantic");
                var offset = parseInt(child.getAttribute("offset"));
                var set = parseInt(child.getAttribute("set"));
                var inputname = set > 0 ? semantic + set : semantic;
                primitive.inputs[inputname] = {
                  id: id,
                  offset: offset
                };
                primitive.stride = Math.max(primitive.stride, offset + 1);
                if (semantic === "TEXCOORD") primitive.hasUV = true;
                break;

              case "vcount":
                primitive.vcount = parseInts(child.textContent);
                break;

              case "p":
                primitive.p = parseInts(child.textContent);
                break;
            }
          }

          return primitive;
        }

        function groupPrimitives(primitives) {
          var build = {};

          for (var i = 0; i < primitives.length; i++) {
            var primitive = primitives[i];
            if (build[primitive.type] === undefined) build[primitive.type] = [];
            build[primitive.type].push(primitive);
          }

          return build;
        }

        function checkUVCoordinates(primitives) {
          var count = 0;

          for (var i = 0, l = primitives.length; i < l; i++) {
            var primitive = primitives[i];

            if (primitive.hasUV === true) {
              count++;
            }
          }

          if (count > 0 && count < primitives.length) {
            primitives.uvsNeedsFix = true;
          }
        }

        function buildGeometry(data) {
          var build = {};
          var sources = data.sources;
          var vertices = data.vertices;
          var primitives = data.primitives;
          if (primitives.length === 0) return {}; // our goal is to create one buffer geometry for a single type of primitives
          // first, we group all primitives by their type

          var groupedPrimitives = groupPrimitives(primitives);

          for (var type in groupedPrimitives) {
            var primitiveType = groupedPrimitives[type]; // second, ensure consistent uv coordinates for each type of primitives (polylist,triangles or lines)

            checkUVCoordinates(primitiveType); // third, create a buffer geometry for each type of primitives

            build[type] = buildGeometryType(primitiveType, sources, vertices);
          }

          return build;
        }

        function buildGeometryType(primitives, sources, vertices) {
          var build = {};
          var position = {
            array: [],
            stride: 0
          };
          var normal = {
            array: [],
            stride: 0
          };
          var uv = {
            array: [],
            stride: 0
          };
          var uv2 = {
            array: [],
            stride: 0
          };
          var color = {
            array: [],
            stride: 0
          };
          var skinIndex = {
            array: [],
            stride: 4
          };
          var skinWeight = {
            array: [],
            stride: 4
          };
          var geometry = new THREE.BufferGeometry();
          var materialKeys = [];
          var start = 0;

          for (var p = 0; p < primitives.length; p++) {
            var primitive = primitives[p];
            var inputs = primitive.inputs; // groups

            var _count = 0;

            switch (primitive.type) {
              case "lines":
              case "linestrips":
                _count = primitive.count * 2;
                break;

              case "triangles":
                _count = primitive.count * 3;
                break;

              case "polylist":
                for (var g = 0; g < primitive.count; g++) {
                  var vc = primitive.vcount[g];

                  switch (vc) {
                    case 3:
                      _count += 3; // single triangle

                      break;

                    case 4:
                      _count += 6; // quad, subdivided into two triangles

                      break;

                    default:
                      _count += (vc - 2) * 3; // polylist with more than four vertices

                      break;
                  }
                }

                break;

              default:
                console.warn("THREE.ColladaLoader: Unknow primitive type:", primitive.type);
            }

            geometry.addGroup(start, _count, p);
            start += _count; // material

            if (primitive.material) {
              materialKeys.push(primitive.material);
            } // geometry data


            for (var name in inputs) {
              var input = inputs[name];

              switch (name) {
                case "VERTEX":
                  for (var key in vertices) {
                    var id = vertices[key];

                    switch (key) {
                      case "POSITION":
                        var prevLength = position.array.length;
                        buildGeometryData(primitive, sources[id], input.offset, position.array);
                        position.stride = sources[id].stride;

                        if (sources.skinWeights && sources.skinIndices) {
                          buildGeometryData(primitive, sources.skinIndices, input.offset, skinIndex.array);
                          buildGeometryData(primitive, sources.skinWeights, input.offset, skinWeight.array);
                        } // see #3803


                        if (primitive.hasUV === false && primitives.uvsNeedsFix === true) {
                          var _count2 = (position.array.length - prevLength) / position.stride;

                          for (var i = 0; i < _count2; i++) {
                            // fill missing uv coordinates
                            uv.array.push(0, 0);
                          }
                        }

                        break;

                      case "NORMAL":
                        buildGeometryData(primitive, sources[id], input.offset, normal.array);
                        normal.stride = sources[id].stride;
                        break;

                      case "COLOR":
                        buildGeometryData(primitive, sources[id], input.offset, color.array);
                        color.stride = sources[id].stride;
                        break;

                      case "TEXCOORD":
                        buildGeometryData(primitive, sources[id], input.offset, uv.array);
                        uv.stride = sources[id].stride;
                        break;

                      case "TEXCOORD1":
                        buildGeometryData(primitive, sources[id], input.offset, uv2.array);
                        uv.stride = sources[id].stride;
                        break;

                      default:
                        console.warn('THREE.ColladaLoader: Semantic "%s" not handled in geometry build process.', key);
                    }
                  }

                  break;

                case "NORMAL":
                  buildGeometryData(primitive, sources[input.id], input.offset, normal.array);
                  normal.stride = sources[input.id].stride;
                  break;

                case "COLOR":
                  buildGeometryData(primitive, sources[input.id], input.offset, color.array, true);
                  color.stride = sources[input.id].stride;
                  break;

                case "TEXCOORD":
                  buildGeometryData(primitive, sources[input.id], input.offset, uv.array);
                  uv.stride = sources[input.id].stride;
                  break;

                case "TEXCOORD1":
                  buildGeometryData(primitive, sources[input.id], input.offset, uv2.array);
                  uv2.stride = sources[input.id].stride;
                  break;
              }
            }
          } // build geometry


          if (position.array.length > 0) geometry.setAttribute("position", new THREE.Float32BufferAttribute(position.array, position.stride));
          if (normal.array.length > 0) geometry.setAttribute("normal", new THREE.Float32BufferAttribute(normal.array, normal.stride));
          if (color.array.length > 0) geometry.setAttribute("color", new THREE.Float32BufferAttribute(color.array, color.stride));
          if (uv.array.length > 0) geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uv.array, uv.stride));
          if (uv2.array.length > 0) geometry.setAttribute("uv2", new THREE.Float32BufferAttribute(uv2.array, uv2.stride));
          if (skinIndex.array.length > 0) geometry.setAttribute("skinIndex", new THREE.Float32BufferAttribute(skinIndex.array, skinIndex.stride));
          if (skinWeight.array.length > 0) geometry.setAttribute("skinWeight", new THREE.Float32BufferAttribute(skinWeight.array, skinWeight.stride));
          build.data = geometry;
          build.type = primitives[0].type;
          build.materialKeys = materialKeys;
          return build;
        }

        function buildGeometryData(primitive, source, offset, array) {
          var isColor = arguments.length > 4 && arguments[4] !== undefined ? arguments[4] : false;
          var indices = primitive.p;
          var stride = primitive.stride;
          var vcount = primitive.vcount;

          function pushVector(i) {
            var index = indices[i + offset] * sourceStride;
            var length = index + sourceStride;

            for (; index < length; index++) {
              array.push(sourceArray[index]);
            }

            if (isColor) {
              // convert the vertex colors from srgb to linear if present
              var startIndex = array.length - sourceStride - 1;
              tempColor.setRGB(array[startIndex + 0], array[startIndex + 1], array[startIndex + 2]).convertSRGBToLinear();
              array[startIndex + 0] = tempColor.r;
              array[startIndex + 1] = tempColor.g;
              array[startIndex + 2] = tempColor.b;
            }
          }

          var sourceArray = source.array;
          var sourceStride = source.stride;

          if (primitive.vcount !== undefined) {
            var index = 0;

            for (var i = 0, l = vcount.length; i < l; i++) {
              var _count3 = vcount[i];

              if (_count3 === 4) {
                var a = index + stride * 0;
                var b = index + stride * 1;
                var c = index + stride * 2;
                var d = index + stride * 3;
                pushVector(a);
                pushVector(b);
                pushVector(d);
                pushVector(b);
                pushVector(c);
                pushVector(d);
              } else if (_count3 === 3) {
                var _a = index + stride * 0;

                var _b = index + stride * 1;

                var _c = index + stride * 2;

                pushVector(_a);
                pushVector(_b);
                pushVector(_c);
              } else if (_count3 > 4) {
                for (var k = 1, kl = _count3 - 2; k <= kl; k++) {
                  var _a2 = index + stride * 0;

                  var _b2 = index + stride * k;

                  var _c2 = index + stride * (k + 1);

                  pushVector(_a2);
                  pushVector(_b2);
                  pushVector(_c2);
                }
              }

              index += stride * _count3;
            }
          } else {
            for (var _i = 0, _l = indices.length; _i < _l; _i += stride) {
              pushVector(_i);
            }
          }
        }

        function getGeometry(id) {
          return getBuild(library.geometries[id], buildGeometry);
        } // kinematics


        function parseKinematicsModel(xml) {
          var data = {
            name: xml.getAttribute("name") || "",
            joints: {},
            links: []
          };

          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "technique_common":
                parseKinematicsTechniqueCommon(child, data);
                break;
            }
          }

          library.kinematicsModels[xml.getAttribute("id")] = data;
        }

        function buildKinematicsModel(data) {
          if (data.build !== undefined) return data.build;
          return data;
        }

        function getKinematicsModel(id) {
          return getBuild(library.kinematicsModels[id], buildKinematicsModel);
        }

        function parseKinematicsTechniqueCommon(xml, data) {
          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "joint":
                data.joints[child.getAttribute("sid")] = parseKinematicsJoint(child);
                break;

              case "link":
                data.links.push(parseKinematicsLink(child));
                break;
            }
          }
        }

        function parseKinematicsJoint(xml) {
          var data;

          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "prismatic":
              case "revolute":
                data = parseKinematicsJointParameter(child);
                break;
            }
          }

          return data;
        }

        function parseKinematicsJointParameter(xml) {
          var data = {
            sid: xml.getAttribute("sid"),
            name: xml.getAttribute("name") || "",
            axis: new THREE.Vector3(),
            limits: {
              min: 0,
              max: 0
            },
            type: xml.nodeName,
            "static": false,
            zeroPosition: 0,
            middlePosition: 0
          };

          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "axis":
                var array = parseFloats(child.textContent);
                data.axis.fromArray(array);
                break;

              case "limits":
                var max = child.getElementsByTagName("max")[0];
                var min = child.getElementsByTagName("min")[0];
                data.limits.max = parseFloat(max.textContent);
                data.limits.min = parseFloat(min.textContent);
                break;
            }
          } // if min is equal to or greater than max, consider the joint static


          if (data.limits.min >= data.limits.max) {
            data["static"] = true;
          } // calculate middle position


          data.middlePosition = (data.limits.min + data.limits.max) / 2.0;
          return data;
        }

        function parseKinematicsLink(xml) {
          var data = {
            sid: xml.getAttribute("sid"),
            name: xml.getAttribute("name") || "",
            attachments: [],
            transforms: []
          };

          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "attachment_full":
                data.attachments.push(parseKinematicsAttachment(child));
                break;

              case "matrix":
              case "translate":
              case "rotate":
                data.transforms.push(parseKinematicsTransform(child));
                break;
            }
          }

          return data;
        }

        function parseKinematicsAttachment(xml) {
          var data = {
            joint: xml.getAttribute("joint").split("/").pop(),
            transforms: [],
            links: []
          };

          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "link":
                data.links.push(parseKinematicsLink(child));
                break;

              case "matrix":
              case "translate":
              case "rotate":
                data.transforms.push(parseKinematicsTransform(child));
                break;
            }
          }

          return data;
        }

        function parseKinematicsTransform(xml) {
          var data = {
            type: xml.nodeName
          };
          var array = parseFloats(xml.textContent);

          switch (data.type) {
            case "matrix":
              data.obj = new THREE.Matrix4();
              data.obj.fromArray(array).transpose();
              break;

            case "translate":
              data.obj = new THREE.Vector3();
              data.obj.fromArray(array);
              break;

            case "rotate":
              data.obj = new THREE.Vector3();
              data.obj.fromArray(array);
              data.angle = THREE.MathUtils.degToRad(array[3]);
              break;
          }

          return data;
        } // physics


        function parsePhysicsModel(xml) {
          var data = {
            name: xml.getAttribute("name") || "",
            rigidBodies: {}
          };

          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "rigid_body":
                data.rigidBodies[child.getAttribute("name")] = {};
                parsePhysicsRigidBody(child, data.rigidBodies[child.getAttribute("name")]);
                break;
            }
          }

          library.physicsModels[xml.getAttribute("id")] = data;
        }

        function parsePhysicsRigidBody(xml, data) {
          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "technique_common":
                parsePhysicsTechniqueCommon(child, data);
                break;
            }
          }
        }

        function parsePhysicsTechniqueCommon(xml, data) {
          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "inertia":
                data.inertia = parseFloats(child.textContent);
                break;

              case "mass":
                data.mass = parseFloats(child.textContent)[0];
                break;
            }
          }
        } // scene


        function parseKinematicsScene(xml) {
          var data = {
            bindJointAxis: []
          };

          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "bind_joint_axis":
                data.bindJointAxis.push(parseKinematicsBindJointAxis(child));
                break;
            }
          }

          library.kinematicsScenes[parseId(xml.getAttribute("url"))] = data;
        }

        function parseKinematicsBindJointAxis(xml) {
          var data = {
            target: xml.getAttribute("target").split("/").pop()
          };

          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            switch (child.nodeName) {
              case "axis":
                var param = child.getElementsByTagName("param")[0];
                data.axis = param.textContent;
                var tmpJointIndex = data.axis.split("inst_").pop().split("axis")[0];
                data.jointIndex = tmpJointIndex.substring(0, tmpJointIndex.length - 1);
                break;
            }
          }

          return data;
        }

        function buildKinematicsScene(data) {
          if (data.build !== undefined) return data.build;
          return data;
        }

        function getKinematicsScene(id) {
          return getBuild(library.kinematicsScenes[id], buildKinematicsScene);
        }

        function setupKinematics() {
          var kinematicsModelId = Object.keys(library.kinematicsModels)[0];
          var kinematicsSceneId = Object.keys(library.kinematicsScenes)[0];
          var visualSceneId = Object.keys(library.visualScenes)[0];
          if (kinematicsModelId === undefined || kinematicsSceneId === undefined) return;
          var kinematicsModel = getKinematicsModel(kinematicsModelId);
          var kinematicsScene = getKinematicsScene(kinematicsSceneId);
          var visualScene = getVisualScene(visualSceneId);
          var bindJointAxis = kinematicsScene.bindJointAxis;
          var jointMap = {};

          for (var i = 0, l = bindJointAxis.length; i < l; i++) {
            var axis = bindJointAxis[i]; // the result of the following query is an element of type 'translate', 'rotate','scale' or 'matrix'

            var targetElement = collada.querySelector('[sid="' + axis.target + '"]');

            if (targetElement) {
              // get the parent of the transform element
              var parentVisualElement = targetElement.parentElement; // connect the joint of the kinematics model with the element in the visual scene

              connect(axis.jointIndex, parentVisualElement);
            }
          }

          function connect(jointIndex, visualElement) {
            var visualElementName = visualElement.getAttribute("name");
            var joint = kinematicsModel.joints[jointIndex];
            visualScene.traverse(function (object) {
              if (object.name === visualElementName) {
                jointMap[jointIndex] = {
                  object: object,
                  transforms: buildTransformList(visualElement),
                  joint: joint,
                  position: joint.zeroPosition
                };
              }
            });
          }

          var m0 = new THREE.Matrix4();
          kinematics = {
            joints: kinematicsModel && kinematicsModel.joints,
            getJointValue: function getJointValue(jointIndex) {
              var jointData = jointMap[jointIndex];

              if (jointData) {
                return jointData.position;
              } else {
                console.warn("THREE.ColladaLoader: Joint " + jointIndex + " doesn't exist.");
              }
            },
            setJointValue: function setJointValue(jointIndex, value) {
              var jointData = jointMap[jointIndex];

              if (jointData) {
                var joint = jointData.joint;

                if (value > joint.limits.max || value < joint.limits.min) {
                  console.warn("THREE.ColladaLoader: Joint " + jointIndex + " value " + value + " outside of limits (min: " + joint.limits.min + ", max: " + joint.limits.max + ").");
                } else if (joint["static"]) {
                  console.warn("THREE.ColladaLoader: Joint " + jointIndex + " is static.");
                } else {
                  var object = jointData.object;
                  var _axis = joint.axis;
                  var transforms = jointData.transforms;
                  matrix.identity(); // each update, we have to apply all transforms in the correct order

                  for (var _i2 = 0; _i2 < transforms.length; _i2++) {
                    var transform = transforms[_i2]; // if there is a connection of the transform node with a joint, apply the joint value

                    if (transform.sid && transform.sid.indexOf(jointIndex) !== -1) {
                      switch (joint.type) {
                        case "revolute":
                          matrix.multiply(m0.makeRotationAxis(_axis, THREE.MathUtils.degToRad(value)));
                          break;

                        case "prismatic":
                          matrix.multiply(m0.makeTranslation(_axis.x * value, _axis.y * value, _axis.z * value));
                          break;

                        default:
                          console.warn("THREE.ColladaLoader: Unknown joint type: " + joint.type);
                          break;
                      }
                    } else {
                      switch (transform.type) {
                        case "matrix":
                          matrix.multiply(transform.obj);
                          break;

                        case "translate":
                          matrix.multiply(m0.makeTranslation(transform.obj.x, transform.obj.y, transform.obj.z));
                          break;

                        case "scale":
                          matrix.scale(transform.obj);
                          break;

                        case "rotate":
                          matrix.multiply(m0.makeRotationAxis(transform.obj, transform.angle));
                          break;
                      }
                    }
                  }

                  object.matrix.copy(matrix);
                  object.matrix.decompose(object.position, object.quaternion, object.scale);
                  jointMap[jointIndex].position = value;
                }
              } else {
                console.log("THREE.ColladaLoader: " + jointIndex + " does not exist.");
              }
            }
          };
        }

        function buildTransformList(node) {
          var transforms = [];
          var xml = collada.querySelector('[id="' + node.id + '"]');

          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;

            var array = void 0,
                _vector = void 0;

            switch (child.nodeName) {
              case "matrix":
                array = parseFloats(child.textContent);

                var _matrix = new THREE.Matrix4().fromArray(array).transpose();

                transforms.push({
                  sid: child.getAttribute("sid"),
                  type: child.nodeName,
                  obj: _matrix
                });
                break;

              case "translate":
              case "scale":
                array = parseFloats(child.textContent);
                _vector = new THREE.Vector3().fromArray(array);
                transforms.push({
                  sid: child.getAttribute("sid"),
                  type: child.nodeName,
                  obj: _vector
                });
                break;

              case "rotate":
                array = parseFloats(child.textContent);
                _vector = new THREE.Vector3().fromArray(array);
                var angle = THREE.MathUtils.degToRad(array[3]);
                transforms.push({
                  sid: child.getAttribute("sid"),
                  type: child.nodeName,
                  obj: _vector,
                  angle: angle
                });
                break;
            }
          }

          return transforms;
        } // nodes


        function prepareNodes(xml) {
          var elements = xml.getElementsByTagName("node"); // ensure all node elements have id attributes

          for (var i = 0; i < elements.length; i++) {
            var element = elements[i];

            if (element.hasAttribute("id") === false) {
              element.setAttribute("id", generateId());
            }
          }
        }

        var matrix = new THREE.Matrix4();
        var vector = new THREE.Vector3();

        function parseNode(xml) {
          var data = {
            name: xml.getAttribute("name") || "",
            type: xml.getAttribute("type"),
            id: xml.getAttribute("id"),
            sid: xml.getAttribute("sid"),
            matrix: new THREE.Matrix4(),
            nodes: [],
            instanceCameras: [],
            instanceControllers: [],
            instanceLights: [],
            instanceGeometries: [],
            instanceNodes: [],
            transforms: {}
          };

          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];
            if (child.nodeType !== 1) continue;
            var array = void 0;

            switch (child.nodeName) {
              case "node":
                data.nodes.push(child.getAttribute("id"));
                parseNode(child);
                break;

              case "instance_camera":
                data.instanceCameras.push(parseId(child.getAttribute("url")));
                break;

              case "instance_controller":
                data.instanceControllers.push(parseNodeInstance(child));
                break;

              case "instance_light":
                data.instanceLights.push(parseId(child.getAttribute("url")));
                break;

              case "instance_geometry":
                data.instanceGeometries.push(parseNodeInstance(child));
                break;

              case "instance_node":
                data.instanceNodes.push(parseId(child.getAttribute("url")));
                break;

              case "matrix":
                array = parseFloats(child.textContent);
                data.matrix.multiply(matrix.fromArray(array).transpose());
                data.transforms[child.getAttribute("sid")] = child.nodeName;
                break;

              case "translate":
                array = parseFloats(child.textContent);
                vector.fromArray(array);
                data.matrix.multiply(matrix.makeTranslation(vector.x, vector.y, vector.z));
                data.transforms[child.getAttribute("sid")] = child.nodeName;
                break;

              case "rotate":
                array = parseFloats(child.textContent);
                var angle = THREE.MathUtils.degToRad(array[3]);
                data.matrix.multiply(matrix.makeRotationAxis(vector.fromArray(array), angle));
                data.transforms[child.getAttribute("sid")] = child.nodeName;
                break;

              case "scale":
                array = parseFloats(child.textContent);
                data.matrix.scale(vector.fromArray(array));
                data.transforms[child.getAttribute("sid")] = child.nodeName;
                break;

              case "extra":
                break;

              default:
                console.log(child);
            }
          }

          if (hasNode(data.id)) {
            console.warn("THREE.ColladaLoader: There is already a node with ID %s. Exclude current node from further processing.", data.id);
          } else {
            library.nodes[data.id] = data;
          }

          return data;
        }

        function parseNodeInstance(xml) {
          var data = {
            id: parseId(xml.getAttribute("url")),
            materials: {},
            skeletons: []
          };

          for (var i = 0; i < xml.childNodes.length; i++) {
            var child = xml.childNodes[i];

            switch (child.nodeName) {
              case "bind_material":
                var instances = child.getElementsByTagName("instance_material");

                for (var j = 0; j < instances.length; j++) {
                  var instance = instances[j];
                  var symbol = instance.getAttribute("symbol");
                  var target = instance.getAttribute("target");
                  data.materials[symbol] = parseId(target);
                }

                break;

              case "skeleton":
                data.skeletons.push(parseId(child.textContent));
                break;
            }
          }

          return data;
        }

        function buildSkeleton(skeletons, joints) {
          var boneData = [];
          var sortedBoneData = [];
          var i, j, data; // a skeleton can have multiple root bones. collada expresses this
          // situtation with multiple "skeleton" tags per controller instance

          for (i = 0; i < skeletons.length; i++) {
            var skeleton = skeletons[i];
            var root = void 0;

            if (hasNode(skeleton)) {
              root = getNode(skeleton);
              buildBoneHierarchy(root, joints, boneData);
            } else if (hasVisualScene(skeleton)) {
              // handle case where the skeleton refers to the visual scene (#13335)
              var visualScene = library.visualScenes[skeleton];
              var children = visualScene.children;

              for (var _j = 0; _j < children.length; _j++) {
                var child = children[_j];

                if (child.type === "JOINT") {
                  var _root = getNode(child.id);

                  buildBoneHierarchy(_root, joints, boneData);
                }
              }
            } else {
              console.error("THREE.ColladaLoader: Unable to find root bone of skeleton with ID:", skeleton);
            }
          } // sort bone data (the order is defined in the corresponding controller)


          for (i = 0; i < joints.length; i++) {
            for (j = 0; j < boneData.length; j++) {
              data = boneData[j];

              if (data.bone.name === joints[i].name) {
                sortedBoneData[i] = data;
                data.processed = true;
                break;
              }
            }
          } // add unprocessed bone data at the end of the list


          for (i = 0; i < boneData.length; i++) {
            data = boneData[i];

            if (data.processed === false) {
              sortedBoneData.push(data);
              data.processed = true;
            }
          } // setup arrays for skeleton creation


          var bones = [];
          var boneInverses = [];

          for (i = 0; i < sortedBoneData.length; i++) {
            data = sortedBoneData[i];
            bones.push(data.bone);
            boneInverses.push(data.boneInverse);
          }

          return new THREE.Skeleton(bones, boneInverses);
        }

        function buildBoneHierarchy(root, joints, boneData) {
          // setup bone data from visual scene
          root.traverse(function (object) {
            if (object.isBone === true) {
              var boneInverse; // retrieve the boneInverse from the controller data

              for (var i = 0; i < joints.length; i++) {
                var joint = joints[i];

                if (joint.name === object.name) {
                  boneInverse = joint.boneInverse;
                  break;
                }
              }

              if (boneInverse === undefined) {
                // Unfortunately, there can be joints in the visual scene that are not part of the
                // corresponding controller. In this case, we have to create a dummy boneInverse matrix
                // for the respective bone. This bone won't affect any vertices, because there are no skin indices
                // and weights defined for it. But we still have to add the bone to the sorted bone list in order to
                // ensure a correct animation of the model.
                boneInverse = new THREE.Matrix4();
              }

              boneData.push({
                bone: object,
                boneInverse: boneInverse,
                processed: false
              });
            }
          });
        }

        function buildNode(data) {
          var objects = [];
          var matrix = data.matrix;
          var nodes = data.nodes;
          var type = data.type;
          var instanceCameras = data.instanceCameras;
          var instanceControllers = data.instanceControllers;
          var instanceLights = data.instanceLights;
          var instanceGeometries = data.instanceGeometries;
          var instanceNodes = data.instanceNodes; // nodes

          for (var i = 0, l = nodes.length; i < l; i++) {
            objects.push(getNode(nodes[i]));
          } // instance cameras


          for (var _i3 = 0, _l2 = instanceCameras.length; _i3 < _l2; _i3++) {
            var instanceCamera = getCamera(instanceCameras[_i3]);

            if (instanceCamera !== null) {
              objects.push(instanceCamera.clone());
            }
          } // instance controllers


          for (var _i4 = 0, _l3 = instanceControllers.length; _i4 < _l3; _i4++) {
            var instance = instanceControllers[_i4];
            var controller = getController(instance.id);
            var geometries = getGeometry(controller.id);
            var newObjects = buildObjects(geometries, instance.materials);
            var skeletons = instance.skeletons;
            var joints = controller.skin.joints;
            var skeleton = buildSkeleton(skeletons, joints);

            for (var j = 0, jl = newObjects.length; j < jl; j++) {
              var _object = newObjects[j];

              if (_object.isSkinnedMesh) {
                _object.bind(skeleton, controller.skin.bindMatrix);

                _object.normalizeSkinWeights();
              }

              objects.push(_object);
            }
          } // instance lights


          for (var _i5 = 0, _l4 = instanceLights.length; _i5 < _l4; _i5++) {
            var instanceLight = getLight(instanceLights[_i5]);

            if (instanceLight !== null) {
              objects.push(instanceLight.clone());
            }
          } // instance geometries


          for (var _i6 = 0, _l5 = instanceGeometries.length; _i6 < _l5; _i6++) {
            var _instance = instanceGeometries[_i6]; // a single geometry instance in collada can lead to multiple object3Ds.
            // this is the case when primitives are combined like triangles and lines

            var _geometries = getGeometry(_instance.id);

            var _newObjects = buildObjects(_geometries, _instance.materials);

            for (var _j2 = 0, _jl = _newObjects.length; _j2 < _jl; _j2++) {
              objects.push(_newObjects[_j2]);
            }
          } // instance nodes


          for (var _i7 = 0, _l6 = instanceNodes.length; _i7 < _l6; _i7++) {
            objects.push(getNode(instanceNodes[_i7]).clone());
          }

          var object;

          if (nodes.length === 0 && objects.length === 1) {
            object = objects[0];
          } else {
            object = type === "JOINT" ? new THREE.Bone() : new THREE.Group();

            for (var _i8 = 0; _i8 < objects.length; _i8++) {
              object.add(objects[_i8]);
            }
          }

          object.name = type === "JOINT" ? data.sid : data.name;
          object.matrix.copy(matrix);
          object.matrix.decompose(object.position, object.quaternion, object.scale);
          return object;
        }

        var fallbackMaterial = new THREE.MeshBasicMaterial({
          color: 0xff00ff
        });

        function resolveMaterialBinding(keys, instanceMaterials) {
          var materials = [];

          for (var i = 0, l = keys.length; i < l; i++) {
            var id = instanceMaterials[keys[i]];

            if (id === undefined) {
              console.warn("THREE.ColladaLoader: Material with key %s not found. Apply fallback material.", keys[i]);
              materials.push(fallbackMaterial);
            } else {
              materials.push(getMaterial(id));
            }
          }

          return materials;
        }

        function buildObjects(geometries, instanceMaterials) {
          var objects = [];

          for (var type in geometries) {
            var geometry = geometries[type];
            var materials = resolveMaterialBinding(geometry.materialKeys, instanceMaterials); // handle case if no materials are defined

            if (materials.length === 0) {
              if (type === "lines" || type === "linestrips") {
                materials.push(new THREE.LineBasicMaterial());
              } else {
                materials.push(new THREE.MeshPhongMaterial());
              }
            } // regard skinning


            var skinning = geometry.data.attributes.skinIndex !== undefined; // choose between a single or multi materials (material array)

            var material = materials.length === 1 ? materials[0] : materials; // now create a specific 3D object

            var object = void 0;

            switch (type) {
              case "lines":
                object = new THREE.LineSegments(geometry.data, material);
                break;

              case "linestrips":
                object = new THREE.Line(geometry.data, material);
                break;

              case "triangles":
              case "polylist":
                if (skinning) {
                  object = new THREE.SkinnedMesh(geometry.data, material);
                } else {
                  object = new THREE.Mesh(geometry.data, material);
                }

                break;
            }

            objects.push(object);
          }

          return objects;
        }

        function hasNode(id) {
          return library.nodes[id] !== undefined;
        }

        function getNode(id) {
          return getBuild(library.nodes[id], buildNode);
        } // visual scenes


        function parseVisualScene(xml) {
          var data = {
            name: xml.getAttribute("name"),
            children: []
          };
          prepareNodes(xml);
          var elements = getElementsByTagName(xml, "node");

          for (var i = 0; i < elements.length; i++) {
            data.children.push(parseNode(elements[i]));
          }

          library.visualScenes[xml.getAttribute("id")] = data;
        }

        function buildVisualScene(data) {
          var group = new THREE.Group();
          group.name = data.name;
          var children = data.children;

          for (var i = 0; i < children.length; i++) {
            var child = children[i];
            group.add(getNode(child.id));
          }

          return group;
        }

        function hasVisualScene(id) {
          return library.visualScenes[id] !== undefined;
        }

        function getVisualScene(id) {
          return getBuild(library.visualScenes[id], buildVisualScene);
        } // scenes


        function parseScene(xml) {
          var instance = getElementsByTagName(xml, "instance_visual_scene")[0];
          return getVisualScene(parseId(instance.getAttribute("url")));
        }

        function setupAnimations() {
          var clips = library.clips;

          if (isEmpty(clips) === true) {
            if (isEmpty(library.animations) === false) {
              // if there are animations but no clips, we create a default clip for playback
              var tracks = [];

              for (var id in library.animations) {
                var animationTracks = getAnimation(id);

                for (var i = 0, l = animationTracks.length; i < l; i++) {
                  tracks.push(animationTracks[i]);
                }
              }

              animations.push(new THREE.AnimationClip("default", -1, tracks));
            }
          } else {
            for (var _id in clips) {
              animations.push(getAnimationClip(_id));
            }
          }
        } // convert the parser error element into text with each child elements text
        // separated by new lines.


        function parserErrorToText(parserError) {
          var result = "";
          var stack = [parserError];

          while (stack.length) {
            var node = stack.shift();

            if (node.nodeType === Node.TEXT_NODE) {
              result += node.textContent;
            } else {
              result += "\n";
              stack.push.apply(stack, node.childNodes);
            }
          }

          return result.trim();
        }

        if (text.length === 0) {
          return {
            scene: new THREE.Scene()
          };
        } // A name or id could be a string enclosed by angle brackets like
        // "<name>". A name like this will not be parsed correctly by the
        // DOMParser, so we remove the angle brackets.


        text = text.replace(/"\<(.*?)\>"/g, '"$1" '); // Single quote version

        text = text.replace(/'\<(.*?)\>'/g, '"$1" ');
        var xml = new DOMParser().parseFromString(text, "application/xml");
        var collada = getElementsByTagName(xml, "COLLADA")[0];
        var parserError = xml.getElementsByTagName("parsererror")[0];

        if (parserError !== undefined) {
          // Chrome will return parser error with a div in it
          var errorElement = getElementsByTagName(parserError, "div")[0];
          var errorText;

          if (errorElement) {
            errorText = errorElement.textContent;
          } else {
            errorText = parserErrorToText(parserError);
          }

          console.error("THREE.ColladaLoader: Failed to parse collada file.\n", errorText);
          return null;
        } // metadata


        var version = collada.getAttribute("version");
        console.log("THREE.ColladaLoader: File version", version);
        var asset = parseAsset(getElementsByTagName(collada, "asset")[0]); // Allows internal methods to access the cache.

        var scope = this;
        var textureLoader = new THREE.TextureLoader(this.manager);
        textureLoader.setPath(this.resourcePath || path).setCrossOrigin(this.crossOrigin); // Change the texture loader, if the requestHeader is present.
        // Texture Loaders use an Image Loader internally, instead of a File Loader.
        // Image Loader uses an img tag, and their src request doesn't accept custom headers.
        // See https://github.com/mrdoob/three.js/issues/10439

        if (scope.requestHeader && Object.keys(scope.requestHeader).length > 0) {
          textureLoader.load = function (url, onLoad, onProgress, onError) {
            var fileLoader = new THREE.FileLoader(scope.manager);
            fileLoader.setPath(this.path).setCrossOrigin(scope.crossOrigin);
            fileLoader.setResponseType("blob");
            fileLoader.setRequestHeader(scope.requestHeader);
            var texture = new THREE.Texture();
            var image = document.createElementNS("http://www.w3.org/1999/xhtml", "img"); // Once the image is loaded, we need to revoke the ObjectURL.

            image.onload = function () {
              image.onload = null;
              URL.revokeObjectURL(image.src);

              if (onLoad) {
                onLoad(image);
              }

              texture.image = image;
              texture.needsUpdate = true;
              scope.manager.itemEnd(url);
            };

            image.onerror = onError; // Once the image is loaded, we need to revoke the ObjectURL.

            fileLoader.load(url, function (blob) {
              image.src = URL.createObjectURL(blob);
            }, onProgress, onError);
            scope.manager.itemStart(url);
            return texture;
          };
        }

        var tgaLoader;

        if (TGALoader) {
          tgaLoader = new TGALoader(this.manager);
          tgaLoader.setPath(this.resourcePath || path);

          if (scope.requestHeader && Object.keys(scope.requestHeader).length > 0) {
            tgaLoader.setRequestHeader(scope.requestHeader);
          }
        } //


        var tempColor = new THREE.Color();
        var animations = [];
        var kinematics = {};
        var count = 0; //

        var library = {
          animations: {},
          clips: {},
          controllers: {},
          images: {},
          effects: {},
          materials: {},
          cameras: {},
          lights: {},
          geometries: {},
          nodes: {},
          visualScenes: {},
          kinematicsModels: {},
          physicsModels: {},
          kinematicsScenes: {}
        };
        parseLibrary(collada, "library_animations", "animation", parseAnimation);
        parseLibrary(collada, "library_animation_clips", "animation_clip", parseAnimationClip);
        parseLibrary(collada, "library_controllers", "controller", parseController);
        parseLibrary(collada, "library_images", "image", parseImage);
        parseLibrary(collada, "library_effects", "effect", parseEffect);
        parseLibrary(collada, "library_materials", "material", parseMaterial);
        parseLibrary(collada, "library_cameras", "camera", parseCamera);
        parseLibrary(collada, "library_lights", "light", parseLight);
        parseLibrary(collada, "library_geometries", "geometry", parseGeometry);
        parseLibrary(collada, "library_nodes", "node", parseNode);
        parseLibrary(collada, "library_visual_scenes", "visual_scene", parseVisualScene);
        parseLibrary(collada, "library_kinematics_models", "kinematics_model", parseKinematicsModel);
        parseLibrary(collada, "library_physics_models", "physics_model", parsePhysicsModel);
        parseLibrary(collada, "scene", "instance_kinematics_scene", parseKinematicsScene);
        buildLibrary(library.animations, buildAnimation);
        buildLibrary(library.clips, buildAnimationClip);
        buildLibrary(library.controllers, buildController);
        buildLibrary(library.images, buildImage);
        buildLibrary(library.effects, buildEffect);
        buildLibrary(library.materials, buildMaterial);
        buildLibrary(library.cameras, buildCamera);
        buildLibrary(library.lights, buildLight);
        buildLibrary(library.geometries, buildGeometry);
        buildLibrary(library.visualScenes, buildVisualScene);
        setupAnimations();
        setupKinematics();
        var scene = parseScene(getElementsByTagName(collada, "scene")[0]);
        scene.animations = animations;

        scene.scale.multiplyScalar(asset.unit);
        return {
          get animations() {
            console.warn("THREE.ColladaLoader: Please access animations over scene.animations now.");
            return animations;
          },

          kinematics: kinematics,
          library: library,
          scene: scene
        };
      }
    }]);

    return ColladaLoader;
  }(THREE.Loader);

  // channel.

  var Color = /*#__PURE__*/function (_THREE$Color) {
    _inherits(Color, _THREE$Color);

    var _super = _createSuper(Color);

    function Color(r, g, b, a) {
      var _this;

      _classCallCheck(this, Color);

      _this = _super.call(this, r, g, b);
      _this.a = 1.0;

      if (a) {
        _this.a = a;
      }

      return _this;
    }

    return _createClass(Color);
  }(THREE__namespace.Color);

  var DDSLoader = /*#__PURE__*/function (_CompressedTextureLoa) {
    _inherits(DDSLoader, _CompressedTextureLoa);

    var _super = _createSuper(DDSLoader);

    function DDSLoader(manager) {
      _classCallCheck(this, DDSLoader);

      return _super.call(this, manager);
    }

    _createClass(DDSLoader, [{
      key: "parse",
      value: function parse(buffer, loadMipmaps) {
        var dds = {
          isCubemap: false,
          mipmaps: [],
          width: 0,
          height: 0,
          format: null,
          mipmapCount: 1
        }; // Adapted from @toji's DDS utils
        // https://github.com/toji/webgl-texture-utils/blob/master/texture-util/dds.js
        // All values and structures referenced from:
        // http://msdn.microsoft.com/en-us/library/bb943991.aspx/

        var DDS_MAGIC = 0x20534444; // const DDSD_CAPS = 0x1;
        // const DDSD_HEIGHT = 0x2;
        // const DDSD_WIDTH = 0x4;
        // const DDSD_PITCH = 0x8;
        // const DDSD_PIXELFORMAT = 0x1000;

        var DDSD_MIPMAPCOUNT = 0x20000; // const DDSD_LINEARSIZE = 0x80000;
        // const DDSD_DEPTH = 0x800000;
        // const DDSCAPS_COMPLEX = 0x8;
        // const DDSCAPS_MIPMAP = 0x400000;
        // const DDSCAPS_TEXTURE = 0x1000;

        var DDSCAPS2_CUBEMAP = 0x200;
        var DDSCAPS2_CUBEMAP_POSITIVEX = 0x400;
        var DDSCAPS2_CUBEMAP_NEGATIVEX = 0x800;
        var DDSCAPS2_CUBEMAP_POSITIVEY = 0x1000;
        var DDSCAPS2_CUBEMAP_NEGATIVEY = 0x2000;
        var DDSCAPS2_CUBEMAP_POSITIVEZ = 0x4000;
        var DDSCAPS2_CUBEMAP_NEGATIVEZ = 0x8000; // const DDSCAPS2_VOLUME = 0x200000;

        function fourCCToInt32(value) {
          return value.charCodeAt(0) + (value.charCodeAt(1) << 8) + (value.charCodeAt(2) << 16) + (value.charCodeAt(3) << 24);
        }

        function int32ToFourCC(value) {
          return String.fromCharCode(value & 0xff, value >> 8 & 0xff, value >> 16 & 0xff, value >> 24 & 0xff);
        }

        function loadARGBMip(buffer, dataOffset, width, height) {
          var dataLength = width * height * 4;
          var srcBuffer = new Uint8Array(buffer, dataOffset, dataLength);
          var byteArray = new Uint8Array(dataLength);
          var dst = 0;
          var src = 0;

          for (var y = 0; y < height; y++) {
            for (var x = 0; x < width; x++) {
              var b = srcBuffer[src];
              src++;
              var g = srcBuffer[src];
              src++;
              var r = srcBuffer[src];
              src++;
              var a = srcBuffer[src];
              src++;
              byteArray[dst] = r;
              dst++; //r

              byteArray[dst] = g;
              dst++; //g

              byteArray[dst] = b;
              dst++; //b

              byteArray[dst] = a;
              dst++; //a
            }
          }

          return byteArray;
        }

        var FOURCC_DXT1 = fourCCToInt32("DXT1");
        var FOURCC_DXT3 = fourCCToInt32("DXT3");
        var FOURCC_DXT5 = fourCCToInt32("DXT5");
        var FOURCC_ETC1 = fourCCToInt32("ETC1");
        var headerLengthInt = 31; // The header length in 32 bit ints
        // Offsets into the header array

        var off_magic = 0;
        var off_size = 1;
        var off_flags = 2;
        var off_height = 3;
        var off_width = 4;
        var off_mipmapCount = 7; // const off_pfFlags = 20;

        var off_pfFourCC = 21;
        var off_RGBBitCount = 22;
        var off_RBitMask = 23;
        var off_GBitMask = 24;
        var off_BBitMask = 25;
        var off_ABitMask = 26; // const off_caps = 27;

        var off_caps2 = 28; // const off_caps3 = 29;
        // const off_caps4 = 30;
        // Parse header

        var header = new Int32Array(buffer, 0, headerLengthInt);

        if (header[off_magic] !== DDS_MAGIC) {
          console.error("THREE.DDSLoader.parse: Invalid magic number in DDS header.");
          return dds;
        }

        var blockBytes;
        var fourCC = header[off_pfFourCC];
        var isRGBAUncompressed = false;

        switch (fourCC) {
          case FOURCC_DXT1:
            blockBytes = 8;
            dds.format = THREE.RGB_S3TC_DXT1_Format;
            break;

          case FOURCC_DXT3:
            blockBytes = 16;
            dds.format = THREE.RGBA_S3TC_DXT3_Format;
            break;

          case FOURCC_DXT5:
            blockBytes = 16;
            dds.format = THREE.RGBA_S3TC_DXT5_Format;
            break;

          case FOURCC_ETC1:
            blockBytes = 8;
            dds.format = THREE.RGB_ETC1_Format;
            break;

          default:
            if (header[off_RGBBitCount] === 32 && header[off_RBitMask] & 0xff0000 && header[off_GBitMask] & 0xff00 && header[off_BBitMask] & 0xff && header[off_ABitMask] & 0xff000000) {
              isRGBAUncompressed = true;
              blockBytes = 64;
              dds.format = THREE.RGBAFormat;
            } else {
              console.error("THREE.DDSLoader.parse: Unsupported FourCC code ", int32ToFourCC(fourCC));
              return dds;
            }

        }

        dds.mipmapCount = 1;

        if (header[off_flags] & DDSD_MIPMAPCOUNT && loadMipmaps !== false) {
          dds.mipmapCount = Math.max(1, header[off_mipmapCount]);
        }

        var caps2 = header[off_caps2];
        dds.isCubemap = caps2 & DDSCAPS2_CUBEMAP ? true : false;

        if (dds.isCubemap && (!(caps2 & DDSCAPS2_CUBEMAP_POSITIVEX) || !(caps2 & DDSCAPS2_CUBEMAP_NEGATIVEX) || !(caps2 & DDSCAPS2_CUBEMAP_POSITIVEY) || !(caps2 & DDSCAPS2_CUBEMAP_NEGATIVEY) || !(caps2 & DDSCAPS2_CUBEMAP_POSITIVEZ) || !(caps2 & DDSCAPS2_CUBEMAP_NEGATIVEZ))) {
          console.error("THREE.DDSLoader.parse: Incomplete cubemap faces");
          return dds;
        }

        dds.width = header[off_width];
        dds.height = header[off_height];
        var dataOffset = header[off_size] + 4; // Extract mipmaps buffers

        var faces = dds.isCubemap ? 6 : 1;

        for (var face = 0; face < faces; face++) {
          var width = dds.width;
          var height = dds.height;

          for (var i = 0; i < dds.mipmapCount; i++) {
            var byteArray = void 0,
                dataLength = void 0;

            if (isRGBAUncompressed) {
              byteArray = loadARGBMip(buffer, dataOffset, width, height);
              dataLength = byteArray.length;
            } else {
              dataLength = Math.max(4, width) / 4 * Math.max(4, height) / 4 * blockBytes;
              byteArray = new Uint8Array(buffer, dataOffset, dataLength);
            }

            var mipmap = {
              data: byteArray,
              width: width,
              height: height
            };
            dds.mipmaps.push(mipmap);
            dataOffset += dataLength;
            width = Math.max(width >> 1, 1);
            height = Math.max(height >> 1, 1);
          }
        }

        return dds;
      }
    }]);

    return DDSLoader;
  }(THREE.CompressedTextureLoader);

  var _object_pattern = /^[og]\s*(.+)?/; // mtllib file_reference

  var _material_library_pattern = /^mtllib /; // usemtl material_name

  var _material_use_pattern = /^usemtl /; // usemap map_name

  var _map_use_pattern = /^usemap /;
  var _face_vertex_data_separator_pattern = /\s+/;

  var _vA = new THREE.Vector3();

  var _vB = new THREE.Vector3();

  var _vC = new THREE.Vector3();

  var _ab = new THREE.Vector3();

  var _cb = new THREE.Vector3();

  var _color = new THREE.Color();

  function ParserState() {
    var state = {
      objects: [],
      object: {},
      vertices: [],
      normals: [],
      colors: [],
      uvs: [],
      materials: {},
      materialLibraries: [],
      startObject: function startObject(name, fromDeclaration) {
        // If the current object (initial from reset) is not from a g/o declaration in the parsed
        // file. We need to use it for the first parsed g/o to keep things in sync.
        if (this.object && this.object.fromDeclaration === false) {
          this.object.name = name;
          this.object.fromDeclaration = fromDeclaration !== false;
          return;
        }

        var previousMaterial = this.object && typeof this.object.currentMaterial === "function" ? this.object.currentMaterial() : undefined;

        if (this.object && typeof this.object._finalize === "function") {
          this.object._finalize(true);
        }

        this.object = {
          name: name || "",
          fromDeclaration: fromDeclaration !== false,
          geometry: {
            vertices: [],
            normals: [],
            colors: [],
            uvs: [],
            hasUVIndices: false
          },
          materials: [],
          smooth: true,
          startMaterial: function startMaterial(name, libraries) {
            var previous = this._finalize(false); // New usemtl declaration overwrites an inherited material, except if faces were declared
            // after the material, then it must be preserved for proper MultiMaterial continuation.


            if (previous && (previous.inherited || previous.groupCount <= 0)) {
              this.materials.splice(previous.index, 1);
            }

            var material = {
              index: this.materials.length,
              name: name || "",
              mtllib: Array.isArray(libraries) && libraries.length > 0 ? libraries[libraries.length - 1] : "",
              smooth: previous !== undefined ? previous.smooth : this.smooth,
              groupStart: previous !== undefined ? previous.groupEnd : 0,
              groupEnd: -1,
              groupCount: -1,
              inherited: false,
              clone: function clone(index) {
                var cloned = {
                  index: typeof index === "number" ? index : this.index,
                  name: this.name,
                  mtllib: this.mtllib,
                  smooth: this.smooth,
                  groupStart: 0,
                  groupEnd: -1,
                  groupCount: -1,
                  inherited: false
                };
                cloned.clone = this.clone.bind(cloned);
                return cloned;
              }
            };
            this.materials.push(material);
            return material;
          },
          currentMaterial: function currentMaterial() {
            if (this.materials.length > 0) {
              return this.materials[this.materials.length - 1];
            }

            return undefined;
          },
          _finalize: function _finalize(end) {
            var lastMultiMaterial = this.currentMaterial();

            if (lastMultiMaterial && lastMultiMaterial.groupEnd === -1) {
              lastMultiMaterial.groupEnd = this.geometry.vertices.length / 3;
              lastMultiMaterial.groupCount = lastMultiMaterial.groupEnd - lastMultiMaterial.groupStart;
              lastMultiMaterial.inherited = false;
            } // Ignore objects tail materials if no face declarations followed them before a new o/g started.


            if (end && this.materials.length > 1) {
              for (var mi = this.materials.length - 1; mi >= 0; mi--) {
                if (this.materials[mi].groupCount <= 0) {
                  this.materials.splice(mi, 1);
                }
              }
            } // Guarantee at least one empty material, this makes the creation later more straight forward.


            if (end && this.materials.length === 0) {
              this.materials.push({
                name: "",
                smooth: this.smooth
              });
            }

            return lastMultiMaterial;
          }
        }; // Inherit previous objects material.
        // Spec tells us that a declared material must be set to all objects until a new material is declared.
        // If a usemtl declaration is encountered while this new object is being parsed, it will
        // overwrite the inherited material. Exception being that there was already face declarations
        // to the inherited material, then it will be preserved for proper MultiMaterial continuation.

        if (previousMaterial && previousMaterial.name && typeof previousMaterial.clone === "function") {
          var declared = previousMaterial.clone(0);
          declared.inherited = true;
          this.object.materials.push(declared);
        }

        this.objects.push(this.object);
      },
      finalize: function finalize() {
        if (this.object && typeof this.object._finalize === "function") {
          this.object._finalize(true);
        }
      },
      parseVertexIndex: function parseVertexIndex(value, len) {
        var index = parseInt(value, 10);
        return (index >= 0 ? index - 1 : index + len / 3) * 3;
      },
      parseNormalIndex: function parseNormalIndex(value, len) {
        var index = parseInt(value, 10);
        return (index >= 0 ? index - 1 : index + len / 3) * 3;
      },
      parseUVIndex: function parseUVIndex(value, len) {
        var index = parseInt(value, 10);
        return (index >= 0 ? index - 1 : index + len / 2) * 2;
      },
      addVertex: function addVertex(a, b, c) {
        var src = this.vertices;
        var dst = this.object.geometry.vertices;
        dst.push(src[a + 0], src[a + 1], src[a + 2]);
        dst.push(src[b + 0], src[b + 1], src[b + 2]);
        dst.push(src[c + 0], src[c + 1], src[c + 2]);
      },
      addVertexPoint: function addVertexPoint(a) {
        var src = this.vertices;
        var dst = this.object.geometry.vertices;
        dst.push(src[a + 0], src[a + 1], src[a + 2]);
      },
      addVertexLine: function addVertexLine(a) {
        var src = this.vertices;
        var dst = this.object.geometry.vertices;
        dst.push(src[a + 0], src[a + 1], src[a + 2]);
      },
      addNormal: function addNormal(a, b, c) {
        var src = this.normals;
        var dst = this.object.geometry.normals;
        dst.push(src[a + 0], src[a + 1], src[a + 2]);
        dst.push(src[b + 0], src[b + 1], src[b + 2]);
        dst.push(src[c + 0], src[c + 1], src[c + 2]);
      },
      addFaceNormal: function addFaceNormal(a, b, c) {
        var src = this.vertices;
        var dst = this.object.geometry.normals;

        _vA.fromArray(src, a);

        _vB.fromArray(src, b);

        _vC.fromArray(src, c);

        _cb.subVectors(_vC, _vB);

        _ab.subVectors(_vA, _vB);

        _cb.cross(_ab);

        _cb.normalize();

        dst.push(_cb.x, _cb.y, _cb.z);
        dst.push(_cb.x, _cb.y, _cb.z);
        dst.push(_cb.x, _cb.y, _cb.z);
      },
      addColor: function addColor(a, b, c) {
        var src = this.colors;
        var dst = this.object.geometry.colors;
        if (src[a] !== undefined) dst.push(src[a + 0], src[a + 1], src[a + 2]);
        if (src[b] !== undefined) dst.push(src[b + 0], src[b + 1], src[b + 2]);
        if (src[c] !== undefined) dst.push(src[c + 0], src[c + 1], src[c + 2]);
      },
      addUV: function addUV(a, b, c) {
        var src = this.uvs;
        var dst = this.object.geometry.uvs;
        dst.push(src[a + 0], src[a + 1]);
        dst.push(src[b + 0], src[b + 1]);
        dst.push(src[c + 0], src[c + 1]);
      },
      addDefaultUV: function addDefaultUV() {
        var dst = this.object.geometry.uvs;
        dst.push(0, 0);
        dst.push(0, 0);
        dst.push(0, 0);
      },
      addUVLine: function addUVLine(a) {
        var src = this.uvs;
        var dst = this.object.geometry.uvs;
        dst.push(src[a + 0], src[a + 1]);
      },
      addFace: function addFace(a, b, c, ua, ub, uc, na, nb, nc) {
        var vLen = this.vertices.length;
        var ia = this.parseVertexIndex(a, vLen);
        var ib = this.parseVertexIndex(b, vLen);
        var ic = this.parseVertexIndex(c, vLen);
        this.addVertex(ia, ib, ic);
        this.addColor(ia, ib, ic); // normals

        if (na !== undefined && na !== "") {
          var nLen = this.normals.length;
          ia = this.parseNormalIndex(na, nLen);
          ib = this.parseNormalIndex(nb, nLen);
          ic = this.parseNormalIndex(nc, nLen);
          this.addNormal(ia, ib, ic);
        } else {
          this.addFaceNormal(ia, ib, ic);
        } // uvs


        if (ua !== undefined && ua !== "") {
          var uvLen = this.uvs.length;
          ia = this.parseUVIndex(ua, uvLen);
          ib = this.parseUVIndex(ub, uvLen);
          ic = this.parseUVIndex(uc, uvLen);
          this.addUV(ia, ib, ic);
          this.object.geometry.hasUVIndices = true;
        } else {
          // add placeholder values (for inconsistent face definitions)
          this.addDefaultUV();
        }
      },
      addPointGeometry: function addPointGeometry(vertices) {
        this.object.geometry.type = "Points";
        var vLen = this.vertices.length;

        for (var vi = 0, l = vertices.length; vi < l; vi++) {
          var index = this.parseVertexIndex(vertices[vi], vLen);
          this.addVertexPoint(index);
          this.addColor(index);
        }
      },
      addLineGeometry: function addLineGeometry(vertices, uvs) {
        this.object.geometry.type = "Line";
        var vLen = this.vertices.length;
        var uvLen = this.uvs.length;

        for (var vi = 0, l = vertices.length; vi < l; vi++) {
          this.addVertexLine(this.parseVertexIndex(vertices[vi], vLen));
        }

        for (var uvi = 0, _l = uvs.length; uvi < _l; uvi++) {
          this.addUVLine(this.parseUVIndex(uvs[uvi], uvLen));
        }
      }
    };
    state.startObject("", false);
    return state;
  } //


  var OBJLoader = /*#__PURE__*/function (_Loader) {
    _inherits(OBJLoader, _Loader);

    var _super = _createSuper(OBJLoader);

    function OBJLoader(manager) {
      var _this;

      _classCallCheck(this, OBJLoader);

      _this = _super.call(this, manager);
      _this.materials = null;
      return _this;
    }

    _createClass(OBJLoader, [{
      key: "load",
      value: function load(url, onLoad, onProgress, onError) {
        var scope = this;
        var loader = new THREE.FileLoader(this.manager);
        loader.setPath(this.path);
        loader.setRequestHeader(this.requestHeader);
        loader.setWithCredentials(this.withCredentials);
        loader.load(url, function (text) {
          try {
            onLoad(scope.parse(text));
          } catch (e) {
            if (onError) {
              onError(e);
            } else {
              console.error(e);
            }

            scope.manager.itemError(url);
          }
        }, onProgress, onError);
      }
    }, {
      key: "setMaterials",
      value: function setMaterials(materials) {
        this.materials = materials;
        return this;
      }
    }, {
      key: "parse",
      value: function parse(text) {
        var state = new ParserState();

        if (text.indexOf("\r\n") !== -1) {
          // This is faster than String.split with regex that splits on both
          text = text.replace(/\r\n/g, "\n");
        }

        if (text.indexOf("\\\n") !== -1) {
          // join lines separated by a line continuation character (\)
          text = text.replace(/\\\n/g, "");
        }

        var lines = text.split("\n");
        var result = [];

        for (var i = 0, l = lines.length; i < l; i++) {
          var line = lines[i].trimStart();
          if (line.length === 0) continue;
          var lineFirstChar = line.charAt(0); // @todo invoke passed in handler if any

          if (lineFirstChar === "#") continue;

          if (lineFirstChar === "v") {
            var data = line.split(_face_vertex_data_separator_pattern);

            switch (data[0]) {
              case "v":
                state.vertices.push(parseFloat(data[1]), parseFloat(data[2]), parseFloat(data[3]));

                if (data.length >= 7) {
                  _color.setRGB(parseFloat(data[4]), parseFloat(data[5]), parseFloat(data[6])).convertSRGBToLinear();

                  state.colors.push(_color.r, _color.g, _color.b);
                } else {
                  // if no colors are defined, add placeholders so color and vertex indices match
                  state.colors.push(undefined, undefined, undefined);
                }

                break;

              case "vn":
                state.normals.push(parseFloat(data[1]), parseFloat(data[2]), parseFloat(data[3]));
                break;

              case "vt":
                state.uvs.push(parseFloat(data[1]), parseFloat(data[2]));
                break;
            }
          } else if (lineFirstChar === "f") {
            var lineData = line.slice(1).trim();
            var vertexData = lineData.split(_face_vertex_data_separator_pattern);
            var faceVertices = []; // Parse the face vertex data into an easy to work with format

            for (var j = 0, jl = vertexData.length; j < jl; j++) {
              var vertex = vertexData[j];

              if (vertex.length > 0) {
                var vertexParts = vertex.split("/");
                faceVertices.push(vertexParts);
              }
            } // Draw an edge between the first vertex and all subsequent vertices to form an n-gon


            var v1 = faceVertices[0];

            for (var _j = 1, _jl = faceVertices.length - 1; _j < _jl; _j++) {
              var v2 = faceVertices[_j];
              var v3 = faceVertices[_j + 1];
              state.addFace(v1[0], v2[0], v3[0], v1[1], v2[1], v3[1], v1[2], v2[2], v3[2]);
            }
          } else if (lineFirstChar === "l") {
            var lineParts = line.substring(1).trim().split(" ");
            var lineVertices = [];
            var lineUVs = [];

            if (line.indexOf("/") === -1) {
              lineVertices = lineParts;
            } else {
              for (var li = 0, llen = lineParts.length; li < llen; li++) {
                var parts = lineParts[li].split("/");
                if (parts[0] !== "") lineVertices.push(parts[0]);
                if (parts[1] !== "") lineUVs.push(parts[1]);
              }
            }

            state.addLineGeometry(lineVertices, lineUVs);
          } else if (lineFirstChar === "p") {
            var _lineData = line.slice(1).trim();

            var pointData = _lineData.split(" ");

            state.addPointGeometry(pointData);
          } else if ((result = _object_pattern.exec(line)) !== null) {
            // o object_name
            // or
            // g group_name
            // WORKAROUND: https://bugs.chromium.org/p/v8/issues/detail?id=2869
            // let name = result[ 0 ].slice( 1 ).trim();
            var name = (" " + result[0].slice(1).trim()).slice(1);
            state.startObject(name);
          } else if (_material_use_pattern.test(line)) {
            // material
            state.object.startMaterial(line.substring(7).trim(), state.materialLibraries);
          } else if (_material_library_pattern.test(line)) {
            // mtl file
            state.materialLibraries.push(line.substring(7).trim());
          } else if (_map_use_pattern.test(line)) {
            // the line is parsed but ignored since the loader assumes textures are defined MTL files
            // (according to https://www.okino.com/conv/imp_wave.htm, 'usemap' is the old-style Wavefront texture reference method)
            console.warn('THREE.OBJLoader: Rendering identifier "usemap" not supported. Textures must be defined in MTL files.');
          } else if (lineFirstChar === "s") {
            result = line.split(" "); // smooth shading
            // @todo Handle files that have varying smooth values for a set of faces inside one geometry,
            // but does not define a usemtl for each face set.
            // This should be detected and a dummy material created (later MultiMaterial and geometry groups).
            // This requires some care to not create extra material on each smooth value for "normal" obj files.
            // where explicit usemtl defines geometry groups.
            // Example asset: examples/models/obj/cerberus/Cerberus.obj

            /*
             * http://paulbourke.net/dataformats/obj/
             *
             * From chapter "Grouping" Syntax explanation "s group_number":
             * "group_number is the smoothing group number. To turn off smoothing groups, use a value of 0 or off.
             * Polygonal elements use group numbers to put elements in different smoothing groups. For free-form
             * surfaces, smoothing groups are either turned on or off; there is no difference between values greater
             * than 0."
             */

            if (result.length > 1) {
              var value = result[1].trim().toLowerCase();
              state.object.smooth = value !== "0" && value !== "off";
            } else {
              // ZBrush can produce "s" lines #11707
              state.object.smooth = true;
            }

            var material = state.object.currentMaterial();
            if (material) material.smooth = state.object.smooth;
          } else {
            // Handle null terminated files without exception
            if (line === "\0") continue;
            console.warn('THREE.OBJLoader: Unexpected line: "' + line + '"');
          }
        }

        state.finalize();
        var container = new THREE.Group();
        container.materialLibraries = [].concat(state.materialLibraries);
        var hasPrimitives = !(state.objects.length === 1 && state.objects[0].geometry.vertices.length === 0);

        if (hasPrimitives === true) {
          for (var _i = 0, _l2 = state.objects.length; _i < _l2; _i++) {
            var object = state.objects[_i];
            var geometry = object.geometry;
            var materials = object.materials;
            var isLine = geometry.type === "Line";
            var isPoints = geometry.type === "Points";
            var hasVertexColors = false; // Skip o/g line declarations that did not follow with any faces

            if (geometry.vertices.length === 0) continue;
            var buffergeometry = new THREE.BufferGeometry();
            buffergeometry.setAttribute("position", new THREE.Float32BufferAttribute(geometry.vertices, 3));

            if (geometry.normals.length > 0) {
              buffergeometry.setAttribute("normal", new THREE.Float32BufferAttribute(geometry.normals, 3));
            }

            if (geometry.colors.length > 0) {
              hasVertexColors = true;
              buffergeometry.setAttribute("color", new THREE.Float32BufferAttribute(geometry.colors, 3));
            }

            if (geometry.hasUVIndices === true) {
              buffergeometry.setAttribute("uv", new THREE.Float32BufferAttribute(geometry.uvs, 2));
            } // Create materials


            var createdMaterials = [];

            for (var mi = 0, miLen = materials.length; mi < miLen; mi++) {
              var sourceMaterial = materials[mi];
              var materialHash = sourceMaterial.name + "_" + sourceMaterial.smooth + "_" + hasVertexColors;
              var _material = state.materials[materialHash];

              if (this.materials !== null) {
                _material = this.materials.create(sourceMaterial.name); // mtl etc. loaders probably can't create line materials correctly, copy properties to a line material.

                if (isLine && _material && !(_material instanceof THREE.LineBasicMaterial)) {
                  var materialLine = new THREE.LineBasicMaterial();
                  THREE.Material.prototype.copy.call(materialLine, _material);
                  materialLine.color.copy(_material.color);
                  _material = materialLine;
                } else if (isPoints && _material && !(_material instanceof THREE.PointsMaterial)) {
                  var materialPoints = new THREE.PointsMaterial({
                    size: 10,
                    sizeAttenuation: false
                  });
                  THREE.Material.prototype.copy.call(materialPoints, _material);
                  materialPoints.color.copy(_material.color);
                  materialPoints.map = _material.map;
                  _material = materialPoints;
                }
              }

              if (_material === undefined) {
                if (isLine) {
                  _material = new THREE.LineBasicMaterial();
                } else if (isPoints) {
                  _material = new THREE.PointsMaterial({
                    size: 1,
                    sizeAttenuation: false
                  });
                } else {
                  _material = new THREE.MeshPhongMaterial();
                }

                _material.name = sourceMaterial.name;
                _material.flatShading = sourceMaterial.smooth ? false : true;
                _material.vertexColors = hasVertexColors;
                state.materials[materialHash] = _material;
              }

              createdMaterials.push(_material);
            } // Create mesh


            var mesh = void 0;

            if (createdMaterials.length > 1) {
              for (var _mi = 0, _miLen = materials.length; _mi < _miLen; _mi++) {
                var _sourceMaterial = materials[_mi];
                buffergeometry.addGroup(_sourceMaterial.groupStart, _sourceMaterial.groupCount, _mi);
              }

              if (isLine) {
                mesh = new THREE.LineSegments(buffergeometry, createdMaterials);
              } else if (isPoints) {
                mesh = new THREE.Points(buffergeometry, createdMaterials);
              } else {
                mesh = new THREE.Mesh(buffergeometry, createdMaterials);
              }
            } else {
              if (isLine) {
                mesh = new THREE.LineSegments(buffergeometry, createdMaterials[0]);
              } else if (isPoints) {
                mesh = new THREE.Points(buffergeometry, createdMaterials[0]);
              } else {
                mesh = new THREE.Mesh(buffergeometry, createdMaterials[0]);
              }
            }

            mesh.name = object.name;
            container.add(mesh);
          }
        } else {
          // if there is only the default parser state object with no geometry data, interpret data as point cloud
          if (state.vertices.length > 0) {
            var _material2 = new THREE.PointsMaterial({
              size: 1,
              sizeAttenuation: false
            });

            var _buffergeometry = new THREE.BufferGeometry();

            _buffergeometry.setAttribute("position", new THREE.Float32BufferAttribute(state.vertices, 3));

            if (state.colors.length > 0 && state.colors[0] !== undefined) {
              _buffergeometry.setAttribute("color", new THREE.Float32BufferAttribute(state.colors, 3));

              _material2.vertexColors = true;
            }

            var points = new THREE.Points(_buffergeometry, _material2);
            container.add(points);
          }
        }

        return container;
      }
    }]);

    return OBJLoader;
  }(THREE.Loader);

  /**
   * Loads a Wavefront .mtl file specifying materials
   */

  var MTLLoader = /*#__PURE__*/function (_Loader) {
    _inherits(MTLLoader, _Loader);

    var _super = _createSuper(MTLLoader);

    function MTLLoader(manager) {
      _classCallCheck(this, MTLLoader);

      return _super.call(this, manager);
    }
    /**
     * Loads and parses a MTL asset from a URL.
     *
     * @param {String} url - URL to the MTL file.
     * @param {Function} [onLoad] - Callback invoked with the loaded object.
     * @param {Function} [onProgress] - Callback for download progress.
     * @param {Function} [onError] - Callback for download errors.
     *
     * @see setPath setResourcePath
     *
     * @note In order for relative texture references to resolve correctly
     * you must call setResourcePath() explicitly prior to load.
     */


    _createClass(MTLLoader, [{
      key: "load",
      value: function load(url, onLoad, onProgress, onError) {
        var scope = this;
        var path = this.path === "" ? THREE.LoaderUtils.extractUrlBase(url) : this.path;
        var loader = new THREE.FileLoader(this.manager);
        loader.setPath(this.path);
        loader.setRequestHeader(this.requestHeader);
        loader.setWithCredentials(this.withCredentials);
        loader.load(url, function (text) {
          try {
            onLoad(scope.parse(text, path));
          } catch (e) {
            if (onError) {
              onError(e);
            } else {
              console.error(e);
            }

            scope.manager.itemError(url);
          }
        }, onProgress, onError);
      }
    }, {
      key: "setMaterialOptions",
      value: function setMaterialOptions(value) {
        this.materialOptions = value;
        return this;
      }
      /**
       * Parses a MTL file.
       *
       * @param {String} text - Content of MTL file
       * @return {MaterialCreator}
       *
       * @see setPath setResourcePath
       *
       * @note In order for relative texture references to resolve correctly
       * you must call setResourcePath() explicitly prior to parse.
       */

    }, {
      key: "parse",
      value: function parse(text, path) {
        var lines = text.split("\n");
        var info = {};
        var delimiter_pattern = /\s+/;
        var materialsInfo = {};

        for (var i = 0; i < lines.length; i++) {
          var line = lines[i];
          line = line.trim();

          if (line.length === 0 || line.charAt(0) === "#") {
            // Blank line or comment ignore
            continue;
          }

          var pos = line.indexOf(" ");
          var key = pos >= 0 ? line.substring(0, pos) : line;
          key = key.toLowerCase();
          var value = pos >= 0 ? line.substring(pos + 1) : "";
          value = value.trim();

          if (key === "newmtl") {
            // New material
            info = {
              name: value
            };
            materialsInfo[value] = info;
          } else {
            if (key === "ka" || key === "kd" || key === "ks" || key === "ke") {
              var ss = value.split(delimiter_pattern, 3);
              info[key] = [parseFloat(ss[0]), parseFloat(ss[1]), parseFloat(ss[2])];
            } else {
              info[key] = value;
            }
          }
        }

        var materialCreator = new MaterialCreator(this.resourcePath || path, this.materialOptions);
        materialCreator.setCrossOrigin(this.crossOrigin);
        materialCreator.setManager(this.manager);
        materialCreator.setMaterials(materialsInfo);
        return materialCreator;
      }
    }]);

    return MTLLoader;
  }(THREE.Loader);
  /**
   * Create a new MTLLoader.MaterialCreator
   * @param baseUrl - Url relative to which textures are loaded
   * @param options - Set of options on how to construct the materials
   *                  side: Which side to apply the material
   *                        FrontSide (default), THREE.BackSide, THREE.DoubleSide
   *                  wrap: What type of wrapping to apply for textures
   *                        RepeatWrapping (default), THREE.ClampToEdgeWrapping, THREE.MirroredRepeatWrapping
   *                  normalizeRGB: RGBs need to be normalized to 0-1 from 0-255
   *                                Default: false, assumed to be already normalized
   *                  ignoreZeroRGBs: Ignore values of RGBs (Ka,Kd,Ks) that are all 0's
   *                                  Default: false
   * @constructor
   */


  var MaterialCreator = /*#__PURE__*/function () {
    function MaterialCreator() {
      var baseUrl = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : "";
      var options = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};

      _classCallCheck(this, MaterialCreator);

      this.baseUrl = baseUrl;
      this.options = options;
      this.materialsInfo = {};
      this.materials = {};
      this.materialsArray = [];
      this.nameLookup = {};
      this.crossOrigin = "anonymous";
      this.side = this.options.side !== undefined ? this.options.side : THREE.FrontSide;
      this.wrap = this.options.wrap !== undefined ? this.options.wrap : THREE.RepeatWrapping;
    }

    _createClass(MaterialCreator, [{
      key: "setCrossOrigin",
      value: function setCrossOrigin(value) {
        this.crossOrigin = value;
        return this;
      }
    }, {
      key: "setManager",
      value: function setManager(value) {
        this.manager = value;
      }
    }, {
      key: "setMaterials",
      value: function setMaterials(materialsInfo) {
        this.materialsInfo = this.convert(materialsInfo);
        this.materials = {};
        this.materialsArray = [];
        this.nameLookup = {};
      }
    }, {
      key: "convert",
      value: function convert(materialsInfo) {
        if (!this.options) return materialsInfo;
        var converted = {};

        for (var mn in materialsInfo) {
          // Convert materials info into normalized form based on options
          var mat = materialsInfo[mn];
          var covmat = {};
          converted[mn] = covmat;

          for (var prop in mat) {
            var save = true;
            var value = mat[prop];
            var lprop = prop.toLowerCase();

            switch (lprop) {
              case "kd":
              case "ka":
              case "ks":
                // Diffuse color (color under white light) using RGB values
                if (this.options && this.options.normalizeRGB) {
                  value = [value[0] / 255, value[1] / 255, value[2] / 255];
                }

                if (this.options && this.options.ignoreZeroRGBs) {
                  if (value[0] === 0 && value[1] === 0 && value[2] === 0) {
                    // ignore
                    save = false;
                  }
                }

                break;
            }

            if (save) {
              covmat[lprop] = value;
            }
          }
        }

        return converted;
      }
    }, {
      key: "preload",
      value: function preload() {
        for (var mn in this.materialsInfo) {
          this.create(mn);
        }
      }
    }, {
      key: "getIndex",
      value: function getIndex(materialName) {
        return this.nameLookup[materialName];
      }
    }, {
      key: "getAsArray",
      value: function getAsArray() {
        var index = 0;

        for (var mn in this.materialsInfo) {
          this.materialsArray[index] = this.create(mn);
          this.nameLookup[mn] = index;
          index++;
        }

        return this.materialsArray;
      }
    }, {
      key: "create",
      value: function create(materialName) {
        if (this.materials[materialName] === undefined) {
          this.createMaterial_(materialName);
        }

        return this.materials[materialName];
      }
    }, {
      key: "createMaterial_",
      value: function createMaterial_(materialName) {
        // Create material
        var scope = this;
        var mat = this.materialsInfo[materialName];
        var params = {
          name: materialName,
          side: this.side
        };

        function resolveURL(baseUrl, url) {
          if (typeof url !== "string" || url === "") return ""; // Absolute URL

          if (/^https?:\/\//i.test(url)) return url;
          return baseUrl + url;
        }

        function setMapForType(mapType, value) {
          if (params[mapType]) return; // Keep the first encountered texture

          var texParams = scope.getTextureParams(value, params);
          var map = scope.loadTexture(resolveURL(scope.baseUrl, texParams.url));
          map.repeat.copy(texParams.scale);
          map.offset.copy(texParams.offset);
          map.wrapS = scope.wrap;
          map.wrapT = scope.wrap;

          if (mapType === "map" || mapType === "emissiveMap") {
            map.encoding = THREE.sRGBEncoding;
          }

          params[mapType] = map;
        }

        for (var prop in mat) {
          var value = mat[prop];
          var n = void 0;
          if (value === "") continue;

          switch (prop.toLowerCase()) {
            // Ns is material specular exponent
            case "kd":
              // Diffuse color (color under white light) using RGB values
              params.color = new THREE.Color().fromArray(value).convertSRGBToLinear();
              break;

            case "ks":
              // Specular color (color when light is reflected from shiny surface) using RGB values
              params.specular = new THREE.Color().fromArray(value).convertSRGBToLinear();
              break;

            case "ke":
              // Emissive using RGB values
              params.emissive = new THREE.Color().fromArray(value).convertSRGBToLinear();
              break;

            case "map_kd":
              // Diffuse texture map
              setMapForType("map", value);
              break;

            case "map_ks":
              // Specular map
              setMapForType("specularMap", value);
              break;

            case "map_ke":
              // Emissive map
              setMapForType("emissiveMap", value);
              break;

            case "norm":
              setMapForType("normalMap", value);
              break;

            case "map_bump":
            case "bump":
              // Bump texture map
              setMapForType("bumpMap", value);
              break;

            case "map_d":
              // Alpha map
              setMapForType("alphaMap", value);
              params.transparent = true;
              break;

            case "ns":
              // The specular exponent (defines the focus of the specular highlight)
              // A high exponent results in a tight, concentrated highlight. Ns values normally range from 0 to 1000.
              params.shininess = parseFloat(value);
              break;

            case "d":
              n = parseFloat(value);

              if (n < 1) {
                params.opacity = n;
                params.transparent = true;
              }

              break;

            case "tr":
              n = parseFloat(value);
              if (this.options && this.options.invertTrProperty) n = 1 - n;

              if (n > 0) {
                params.opacity = 1 - n;
                params.transparent = true;
              }

              break;
          }
        }

        this.materials[materialName] = new THREE.MeshPhongMaterial(params);
        return this.materials[materialName];
      }
    }, {
      key: "getTextureParams",
      value: function getTextureParams(value, matParams) {
        var texParams = {
          scale: new THREE.Vector2(1, 1),
          offset: new THREE.Vector2(0, 0)
        };
        var items = value.split(/\s+/);
        var pos;
        pos = items.indexOf("-bm");

        if (pos >= 0) {
          matParams.bumpScale = parseFloat(items[pos + 1]);
          items.splice(pos, 2);
        }

        pos = items.indexOf("-s");

        if (pos >= 0) {
          texParams.scale.set(parseFloat(items[pos + 1]), parseFloat(items[pos + 2]));
          items.splice(pos, 4); // we expect 3 parameters here!
        }

        pos = items.indexOf("-o");

        if (pos >= 0) {
          texParams.offset.set(parseFloat(items[pos + 1]), parseFloat(items[pos + 2]));
          items.splice(pos, 4); // we expect 3 parameters here!
        }

        texParams.url = items.join(" ").trim();
        return texParams;
      }
    }, {
      key: "loadTexture",
      value: function loadTexture(url, mapping, onLoad, onProgress, onError) {
        var manager = this.manager !== undefined ? this.manager : THREE.DefaultLoadingManager;
        var loader = manager.getHandler(url);

        if (loader === null) {
          loader = new THREE.TextureLoader(manager);
        }

        if (loader.setCrossOrigin) loader.setCrossOrigin(this.crossOrigin);
        var texture = loader.load(url, onLoad, onProgress, onError);
        if (mapping !== undefined) texture.mapping = mapping;
        return texture;
      }
    }]);

    return MaterialCreator;
  }();

  var GzObjLoader = /*#__PURE__*/function () {
    /**
     * Load OBJ meshes
     *
     * @constructor
     *
     * @param {Scene} _scene - The scene to load into
     * @param {string} _uri - mesh uri which is used by mtlloader and the objloader
     * to load both the mesh file and the mtl file using XMLHttpRequests.
     * @param {} _submesh
     * @param {} _centerSubmesh
     * @param {function(resource)} _findResourceCb - A function callback that can be used to help
     * @param {function} _onLoad
     * @param {array} _files -optional- the obj [0] and the mtl [1] files as strings
     * to be parsed by the loaders, if provided the uri will not be used just
     * as a url, no XMLHttpRequest will be made.
     */
    function GzObjLoader(_scene, _uri, _submesh, _centerSubmesh, _findResourceCb, _onLoad, _onError, _files) {
      _classCallCheck(this, GzObjLoader);

      this.uri = "";
      this.baseUrl = "";
      this.files = [];
      this.usingRawFiles = false;
      this.objLoader = new OBJLoader();
      this.mtlLoader = new MTLLoader(); // Keep parameters

      this.scene = _scene;
      this.submesh = _submesh;
      this.centerSubmesh = _centerSubmesh;
      this.findResourceCb = _findResourceCb;
      this.onLoad = _onLoad;
      this.uri = _uri;

      if (_files) {
        this.files = _files; // True if raw files were provided

        this.usingRawFiles = this.files.length === 2 && this.files[0] !== undefined && this.files[1] !== undefined;
      } // Loaders


      this.mtlLoader.setCrossOrigin("");

      if (this.scene.requestHeader) {
        this.objLoader.setRequestHeader(this.scene.requestHeader);
        this.mtlLoader.setRequestHeader(this.scene.requestHeader);
      } // Assume .mtl is in the same path as .obj


      if (!this.usingRawFiles) {
        var baseUrl = this.uri.substr(0, this.uri.lastIndexOf("/") + 1);
        this.mtlLoader.setResourcePath(baseUrl);
        this.mtlLoader.setPath(baseUrl);
      }
    }
    /**
     * Load Obj file
     */


    _createClass(GzObjLoader, [{
      key: "load",
      value: function load() {
        var that = this; // If no raw files are provided, make HTTP request

        if (!this.usingRawFiles) {
          this.objLoader.load(this.uri, // onLoad
          function (_container) {
            that.onObjLoaded(_container);
          }, // onProgres
          function (_progress) {// Ignore
          }, function (_error) {
            // Use the find resource callback to get the mesh
            that.findResourceCb(that.uri, function (mesh) {
              that.onObjLoaded(that.objLoader.parse(mesh));
            });
          });
        } // Otherwise load from raw file
        else {
          var container = this.objLoader.parse(this.files[0]);
          this.onObjLoaded(container);
        }
      }
      /**
       * Callback when loading is successfully completed
       */

    }, {
      key: "loadComplete",
      value: function loadComplete() {
        var obj = this.container;
        this.scene.meshes[this.uri] = obj;
        obj = obj.clone();
        this.scene.useSubMesh(obj, this.submesh, this.centerSubmesh);
        obj.name = this.uri;
        this.onLoad(obj);
      }
      /**
       * Callback when loading is successfully completed
       * @param {MTLLoaderMaterialCreator} _mtlCreator - Returned by MTLLoader.parse
       */

    }, {
      key: "applyMaterial",
      value: function applyMaterial(_mtlCreator) {
        var allChildren = [];
        getDescendants(this.container, allChildren);

        for (var j = 0; j < allChildren.length; ++j) {
          var child = allChildren[j];

          if (child && child.hasOwnProperty("material")) {
            var childMesh = child;

            if (childMesh.material.name) {
              childMesh.material = _mtlCreator.create(childMesh.material.name);
            } else if (Array.isArray(childMesh.material)) {
              for (var k = 0; k < childMesh.material.length; ++k) {
                childMesh.material[k] = _mtlCreator.create(childMesh.material[k].name);
              }
            }
          }
        }

        this.loadComplete();
      }
      /**
       * Callback when raw .mtl file has been loaded
       *
       * Assumptions:
       *     * Both .obj and .mtl files are under the /meshes dir
       *     * Textures are under the /materials/textures dir
       *
       * Three texture filename patterns are handled. A single .mtl file may
       * have instances of all of these.
       * 1. Path relative to the meshes folder, which should always start with
       *    ../materials/textures/
       * 2. Gazebo URI in the model:// format, referencing another model
       *    in the same path as the one being loaded
       * 2. Just the image filename without a path
       * @param {string} _text - MTL file as string
       */

    }, {
      key: "loadMTL",
      value: function loadMTL(_text) {
        if (!_text) {
          return;
        } // Handle model:// URI


        if (_text.indexOf("model://") > 0) {
          // If there's no path, remove model://
          if (!this.mtlLoader.path || this.mtlLoader.path.length === 0) {
            _text = _text.replace(/model:\/\//g, "");
          } else if (this.mtlLoader.path.indexOf("/meshes/") < 0) {
            console.error("Failed to resolve texture URI. MTL file directory [" + this.mtlLoader.path + "] not supported, it should be in a /meshes directory");
            console.error(_text);
            return;
          } else {
            // Get models path from .mtl file path
            // This assumes the referenced model is in the same path as the model
            // being loaded. So this may fail if there are models being loaded
            // from various paths
            var path = this.mtlLoader.path;
            path = path.substr(0, path.lastIndexOf("/meshes"));
            path = path.substr(0, path.lastIndexOf("/") + 1); // Search and replace

            _text = _text.replace(/model:\/\//g, path);
          }
        } // Handle case in which the image filename is given without a path
        // We expect the texture to be under /materials/textures


        var lines = _text.split("\n");

        if (lines.length === 0) {
          console.error("Empty or no MTL file");
          return;
        }

        var newText = "";

        for (var i in lines) {
          var line = lines[i];

          if (line === undefined || line.indexOf("#") === 0) {
            continue;
          } // Skip lines without texture filenames


          if (line.indexOf("map_Ka") < 0 && line.indexOf("map_Kd") < 0) {
            newText += line += "\n";
            continue;
          } // Skip lines which already have /materials/textures


          if (line.indexOf("/materials/textures") > 0 && !this.usingRawFiles) {
            newText += line += "\n";
            continue;
          } // Remove ../ from raw files


          if (line.indexOf("../materials/textures") > 0 && this.usingRawFiles) {
            line = line.replace("../", "");
            newText += line += "\n";
            continue;
          } // Add path to filename


          var p = this.mtlLoader.path || "";
          p = p.substr(0, p.lastIndexOf("meshes"));
          line = line.replace("map_Ka ", "map_Ka " + p + "materials/textures/");
          line = line.replace("map_Kd ", "map_Kd " + p + "materials/textures/");
          newText += line += "\n";
        }

        this.applyMaterial(this.mtlLoader.parse(newText, null));
      }
      /**
       * Callback when OBJ file has been loaded, proceeds to load MTL.
       * @param {obj} _container - Loaded OBJ.
       */

    }, {
      key: "onObjLoaded",
      value: function onObjLoaded(_container) {
        var _this = this;

        this.container = _container; // Callback when MTL has been loaded
        // Linter doesn't like `that` being used inside a loop, so we move it outside

        var that = this;

        if (this.container.materialLibraries.length === 0) {
          // return if there are no materials to be applied
          this.loadComplete();
          return;
        } // Load all MTL files


        if (!this.usingRawFiles) {
          var _loop = function _loop() {
            // Load raw .mtl file
            var mtlPath = _this.container.materialLibraries[i];
            fileLoader = new THREE.FileLoader(_this.mtlLoader.manager);
            fileLoader.setPath(_this.mtlLoader.path);
            fileLoader.setRequestHeader(_this.mtlLoader.requestHeader);
            fileLoader.load(mtlPath, // onLoad
            function (_text) {
              if (typeof _text === "string") {
                that.loadMTL(_text);
              } else {
                console.error("Unable to load file", mtlPath);
              }
            });
          };

          for (var i = 0; i < this.container.materialLibraries.length; ++i) {
            var fileLoader;

            _loop();
          }
        } // Use provided MTL file
        else {
          this.loadMTL(this.files[1]);
        }
      }
    }]);

    return GzObjLoader;
  }();

  var ModelUserData = /*#__PURE__*/_createClass(function ModelUserData() {
    _classCallCheck(this, ModelUserData);

    this.viewAs = "normal";
  });

  // Unlike TrackballControls, it maintains the "up" direction object.up (+Y by default).
  //
  //    Orbit - left mouse / touch: one-finger move
  //    Zoom - middle mouse, or mousewheel / touch: two-finger spread or squish
  //    Pan - right mouse, or left mouse + ctrl/meta/shiftKey, or arrow keys / touch: two-finger move

  var _changeEvent = {
    type: "change"
  };
  var _startEvent = {
    type: "start"
  };
  var _endEvent = {
    type: "end"
  };

  var OrbitControls = /*#__PURE__*/function (_EventDispatcher) {
    _inherits(OrbitControls, _EventDispatcher);

    var _super = _createSuper(OrbitControls);

    function OrbitControls(object, domElement) {
      var _this;

      _classCallCheck(this, OrbitControls);

      _this = _super.call(this);
      if (domElement === undefined) console.warn('THREE.OrbitControls: The second parameter "domElement" is now mandatory.');
      if (domElement === document) console.error('THREE.OrbitControls: "document" should not be used as the target "domElement". Please use "renderer.domElement" instead.');
      _this.object = object;
      _this.domElement = domElement;
      _this.domElement.style.touchAction = "none"; // disable touch scroll
      // Set to false to disable this control

      _this.enabled = true; // "target" sets the location of focus, where the object orbits around

      _this.target = new THREE.Vector3(); // How far you can dolly in and out ( PerspectiveCamera only )

      _this.minDistance = 0;
      _this.maxDistance = Infinity; // How far you can zoom in and out ( OrthographicCamera only )

      _this.minZoom = 0;
      _this.maxZoom = Infinity; // How far you can orbit vertically, upper and lower limits.
      // Range is 0 to Math.PI radians.

      _this.minPolarAngle = 0; // radians

      _this.maxPolarAngle = Math.PI; // radians
      // How far you can orbit horizontally, upper and lower limits.
      // If set, the interval [ min, max ] must be a sub-interval of [ - 2 PI, 2 PI ], with ( max - min < 2 PI )

      _this.minAzimuthAngle = -Infinity; // radians

      _this.maxAzimuthAngle = Infinity; // radians
      // Set to true to enable damping (inertia)
      // If damping is enabled, you must call controls.update() in your animation loop

      _this.enableDamping = false;
      _this.dampingFactor = 0.05; // This option actually enables dollying in and out; left as "zoom" for backwards compatibility.
      // Set to false to disable zooming

      _this.enableZoom = true;
      _this.zoomSpeed = 1.0; // Set to false to disable rotating

      _this.enableRotate = true;
      _this.rotateSpeed = 1.0; // Set to false to disable panning

      _this.enablePan = true;
      _this.panSpeed = 1.0;
      _this.screenSpacePanning = true; // if false, pan orthogonal to world-space direction camera.up

      _this.keyPanSpeed = 7.0; // pixels moved per arrow key push
      // Set to true to automatically rotate around the target
      // If auto-rotate is enabled, you must call controls.update() in your animation loop

      _this.autoRotate = false;
      _this.autoRotateSpeed = 2.0; // 30 seconds per orbit when fps is 60
      // The four arrow keys

      _this.keys = {
        LEFT: "ArrowLeft",
        UP: "ArrowUp",
        RIGHT: "ArrowRight",
        BOTTOM: "ArrowDown"
      }; // Mouse buttons

      _this.mouseButtons = {
        LEFT: THREE.MOUSE.ROTATE,
        MIDDLE: THREE.MOUSE.DOLLY,
        RIGHT: THREE.MOUSE.PAN
      }; // Touch fingers

      _this.touches = {
        ONE: THREE.TOUCH.ROTATE,
        TWO: THREE.TOUCH.DOLLY_PAN
      }; // for reset

      _this.target0 = _this.target.clone();
      _this.position0 = _this.object.position.clone();
      _this.zoom0 = _this.object.zoom; // the target DOM element for key events

      _this._domElementKeyEvents = null; //
      // public methods
      //

      _this.getPolarAngle = function () {
        return spherical.phi;
      };

      _this.getAzimuthalAngle = function () {
        return spherical.theta;
      };

      _this.getDistance = function () {
        return this.object.position.distanceTo(this.target);
      };

      _this.listenToKeyEvents = function (domElement) {
        domElement.addEventListener("keydown", onKeyDown);
        this._domElementKeyEvents = domElement;
      };

      _this.saveState = function () {
        scope.target0.copy(scope.target);
        scope.position0.copy(scope.object.position);
        scope.zoom0 = scope.object.zoom;
      };

      _this.reset = function () {
        scope.target.copy(scope.target0);
        scope.object.position.copy(scope.position0);
        scope.object.zoom = scope.zoom0;
        scope.object.updateProjectionMatrix();
        scope.dispatchEvent(_changeEvent);
        scope.update();
        state = STATE.NONE;
      }; // this method is exposed, but perhaps it would be better if we can make it private...


      _this.update = function () {
        var offset = new THREE.Vector3(); // so camera.up is the orbit axis

        var quat = new THREE.Quaternion().setFromUnitVectors(object.up, new THREE.Vector3(0, 1, 0));
        var quatInverse = quat.clone().invert();
        var lastPosition = new THREE.Vector3();
        var lastQuaternion = new THREE.Quaternion();
        var twoPI = 2 * Math.PI;
        return function update() {
          var position = scope.object.position;
          offset.copy(position).sub(scope.target); // rotate offset to "y-axis-is-up" space

          offset.applyQuaternion(quat); // angle from z-axis around y-axis

          spherical.setFromVector3(offset);

          if (scope.autoRotate && state === STATE.NONE) {
            rotateLeft(getAutoRotationAngle());
          }

          var oldTheta = spherical.theta;
          var oldPhi = spherical.phi;

          if (scope.enableDamping) {
            spherical.theta += sphericalDelta.theta * scope.dampingFactor;
            spherical.phi += sphericalDelta.phi * scope.dampingFactor;
          } else {
            spherical.theta += sphericalDelta.theta;
            spherical.phi += sphericalDelta.phi;
          } // restrict theta to be between desired limits


          var min = scope.minAzimuthAngle;
          var max = scope.maxAzimuthAngle;

          if (isFinite(min) && isFinite(max)) {
            if (min < -Math.PI) min += twoPI;else if (min > Math.PI) min -= twoPI;
            if (max < -Math.PI) max += twoPI;else if (max > Math.PI) max -= twoPI;

            if (min <= max) {
              spherical.theta = Math.max(min, Math.min(max, spherical.theta));
            } else {
              spherical.theta = spherical.theta > (min + max) / 2 ? Math.max(min, spherical.theta) : Math.min(max, spherical.theta);
            }
          } // restrict phi to be between desired limits


          spherical.phi = Math.max(scope.minPolarAngle, Math.min(scope.maxPolarAngle, spherical.phi));
          spherical.makeSafe();
          spherical.radius *= scale; // restrict radius to be between desired limits

          spherical.radius = Math.max(scope.minDistance, Math.min(scope.maxDistance, spherical.radius)); // move target to panned location

          if (scope.enableDamping === true) {
            scope.target.addScaledVector(panOffset, scope.dampingFactor);
          } else {
            scope.target.add(panOffset);
          }

          offset.setFromSpherical(spherical); // rotate offset back to "camera-up-vector-is-up" space

          offset.applyQuaternion(quatInverse);

          if (Math.abs(sphericalDelta.phi - 0) > 0.001 || Math.abs(sphericalDelta.theta - 0) > 0.001) {
            var rotateAroundWorldAxis = function rotateAroundWorldAxis(object, axis, radians) {
              var rotWorldMatrix = new THREE.Matrix4();
              rotWorldMatrix.makeRotationAxis(axis.normalize(), radians);
              rotWorldMatrix.multiply(object.matrix); // pre-multiply

              rotWorldMatrix.decompose(object.position, object.quaternion, object.scale);
              object.updateMatrix();
            };

            scope.object.position.sub(scope.target);
            scope.object.updateMatrix();
            rotateAroundWorldAxis(scope.object, new THREE.Vector3(0, 0, 1), spherical.theta - oldTheta);
            var localPitch = new THREE.Vector3(1, 0, 0);
            localPitch.applyQuaternion(scope.object.quaternion);
            rotateAroundWorldAxis(scope.object, localPitch, spherical.phi - oldPhi);
            scope.object.position.add(scope.target);
            scope.object.updateMatrix();
          } else {
            position.copy(scope.target).add(offset);
          }

          if (scope.enableDamping === true) {
            sphericalDelta.theta *= 1 - scope.dampingFactor;
            sphericalDelta.phi *= 1 - scope.dampingFactor;
            panOffset.multiplyScalar(1 - scope.dampingFactor);
          } else {
            sphericalDelta.set(0, 0, 0);
            panOffset.set(0, 0, 0);
          }

          scale = 1; // update condition is:
          // min(camera displacement, camera rotation in radians)^2 > EPS
          // using small-angle approximation cos(x/2) = 1 - x^2 / 8

          if (zoomChanged || lastPosition.distanceToSquared(scope.object.position) > EPS || 8 * (1 - lastQuaternion.dot(scope.object.quaternion)) > EPS) {
            scope.dispatchEvent(_changeEvent);
            lastPosition.copy(scope.object.position);
            lastQuaternion.copy(scope.object.quaternion);
            zoomChanged = false;
            return true;
          }

          return false;
        };
      }();

      _this.dispose = function () {
        scope.domElement.removeEventListener("contextmenu", onContextMenu);
        scope.domElement.removeEventListener("pointerdown", onPointerDown);
        scope.domElement.removeEventListener("pointercancel", onPointerCancel);
        scope.domElement.removeEventListener("wheel", onMouseWheel);
        scope.domElement.removeEventListener("pointermove", onPointerMove);
        scope.domElement.removeEventListener("pointerup", onPointerUp);

        if (scope._domElementKeyEvents !== null) {
          scope._domElementKeyEvents.removeEventListener("keydown", onKeyDown);
        } //scope.dispatchEvent( { type: 'dispose' } ); // should this be added here?

      }; //
      // internals
      //


      var scope = _assertThisInitialized(_this);

      var STATE = {
        NONE: -1,
        ROTATE: 0,
        DOLLY: 1,
        PAN: 2,
        TOUCH_ROTATE: 3,
        TOUCH_PAN: 4,
        TOUCH_DOLLY_PAN: 5,
        TOUCH_DOLLY_ROTATE: 6
      };
      var state = STATE.NONE;
      var EPS = 0.000001; // current position in spherical coordinates

      var spherical = new THREE.Spherical();
      var sphericalDelta = new THREE.Spherical();
      var scale = 1;
      var panOffset = new THREE.Vector3();
      var zoomChanged = false;
      var rotateStart = new THREE.Vector2();
      var rotateEnd = new THREE.Vector2();
      var rotateDelta = new THREE.Vector2();
      var panStart = new THREE.Vector2();
      var panEnd = new THREE.Vector2();
      var panDelta = new THREE.Vector2();
      var dollyStart = new THREE.Vector2();
      var dollyEnd = new THREE.Vector2();
      var dollyDelta = new THREE.Vector2();
      var pointers = [];
      var pointerPositions = {};

      function getAutoRotationAngle() {
        return 2 * Math.PI / 60 / 60 * scope.autoRotateSpeed;
      }

      function getZoomScale() {
        return Math.pow(0.95, scope.zoomSpeed);
      }

      function rotateLeft(angle) {
        sphericalDelta.theta -= angle;
      }

      function rotateUp(angle) {
        sphericalDelta.phi -= angle;
      }

      var panLeft = function () {
        var v = new THREE.Vector3();
        return function panLeft(distance, objectMatrix) {
          v.setFromMatrixColumn(objectMatrix, 0); // get X column of objectMatrix

          v.multiplyScalar(-distance);
          panOffset.add(v);
        };
      }();

      var panUp = function () {
        var v = new THREE.Vector3();
        return function panUp(distance, objectMatrix) {
          if (scope.screenSpacePanning === true) {
            v.setFromMatrixColumn(objectMatrix, 1);
          } else {
            v.setFromMatrixColumn(objectMatrix, 0);
            v.crossVectors(scope.object.up, v);
          }

          v.multiplyScalar(distance);
          panOffset.add(v);
        };
      }(); // deltaX and deltaY are in pixels; right and down are positive


      var pan = function () {
        var offset = new THREE.Vector3();
        return function pan(deltaX, deltaY) {
          var element = scope.domElement;

          if (scope.object.isPerspectiveCamera) {
            // perspective
            var position = scope.object.position;
            offset.copy(position).sub(scope.target);
            var targetDistance = offset.length(); // half of the fov is center to top of screen

            targetDistance *= Math.tan(scope.object.fov / 2 * Math.PI / 180.0); // we use only clientHeight here so aspect ratio does not distort speed

            panLeft(2 * deltaX * targetDistance / element.clientHeight, scope.object.matrix);
            panUp(2 * deltaY * targetDistance / element.clientHeight, scope.object.matrix);
          } else if (scope.object.isOrthographicCamera) {
            // orthographic
            panLeft(deltaX * (scope.object.right - scope.object.left) / scope.object.zoom / element.clientWidth, scope.object.matrix);
            panUp(deltaY * (scope.object.top - scope.object.bottom) / scope.object.zoom / element.clientHeight, scope.object.matrix);
          } else {
            // camera neither orthographic nor perspective
            console.warn("WARNING: OrbitControls.js encountered an unknown camera type - pan disabled.");
            scope.enablePan = false;
          }
        };
      }();

      function dollyOut(dollyScale) {
        if (scope.object.isPerspectiveCamera) {
          scale /= dollyScale;
        } else if (scope.object.isOrthographicCamera) {
          scope.object.zoom = Math.max(scope.minZoom, Math.min(scope.maxZoom, scope.object.zoom * dollyScale));
          scope.object.updateProjectionMatrix();
          zoomChanged = true;
        } else {
          console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled.");
          scope.enableZoom = false;
        }
      }

      function dollyIn(dollyScale) {
        if (scope.object.isPerspectiveCamera) {
          scale *= dollyScale;
        } else if (scope.object.isOrthographicCamera) {
          scope.object.zoom = Math.max(scope.minZoom, Math.min(scope.maxZoom, scope.object.zoom / dollyScale));
          scope.object.updateProjectionMatrix();
          zoomChanged = true;
        } else {
          console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled.");
          scope.enableZoom = false;
        }
      } //
      // event callbacks - update the object state
      //


      function handleMouseDownRotate(event) {
        rotateStart.set(event.clientX, event.clientY);
      }

      function handleMouseDownDolly(event) {
        dollyStart.set(event.clientX, event.clientY);
      }

      function handleMouseDownPan(event) {
        panStart.set(event.clientX, event.clientY);
      }

      function handleMouseMoveRotate(event) {
        rotateEnd.set(event.clientX, event.clientY);
        rotateDelta.subVectors(rotateEnd, rotateStart).multiplyScalar(scope.rotateSpeed);
        var element = scope.domElement;
        rotateLeft(2 * Math.PI * rotateDelta.x / element.clientHeight); // yes, height

        rotateUp(2 * Math.PI * rotateDelta.y / element.clientHeight);
        rotateStart.copy(rotateEnd);
        scope.update();
      }

      function handleMouseMoveDolly(event) {
        dollyEnd.set(event.clientX, event.clientY);
        dollyDelta.subVectors(dollyEnd, dollyStart);

        if (dollyDelta.y > 0) {
          dollyOut(getZoomScale());
        } else if (dollyDelta.y < 0) {
          dollyIn(getZoomScale());
        }

        dollyStart.copy(dollyEnd);
        scope.update();
      }

      function handleMouseMovePan(event) {
        panEnd.set(event.clientX, event.clientY);
        panDelta.subVectors(panEnd, panStart).multiplyScalar(scope.panSpeed);
        pan(panDelta.x, panDelta.y);
        panStart.copy(panEnd);
        scope.update();
      }

      function handleMouseWheel(event) {
        if (event.deltaY < 0) {
          dollyIn(getZoomScale());
        } else if (event.deltaY > 0) {
          dollyOut(getZoomScale());
        }

        scope.update();
      }

      function handleKeyDown(event) {
        var needsUpdate = false;

        switch (event.code) {
          case scope.keys.UP:
            pan(0, scope.keyPanSpeed);
            needsUpdate = true;
            break;

          case scope.keys.BOTTOM:
            pan(0, -scope.keyPanSpeed);
            needsUpdate = true;
            break;

          case scope.keys.LEFT:
            pan(scope.keyPanSpeed, 0);
            needsUpdate = true;
            break;

          case scope.keys.RIGHT:
            pan(-scope.keyPanSpeed, 0);
            needsUpdate = true;
            break;
        }

        if (needsUpdate) {
          // prevent the browser from scrolling on cursor keys
          event.preventDefault();
          scope.update();
        }
      }

      function handleTouchStartRotate() {
        if (pointers.length === 1) {
          rotateStart.set(pointers[0].pageX, pointers[0].pageY);
        } else {
          var x = 0.5 * (pointers[0].pageX + pointers[1].pageX);
          var y = 0.5 * (pointers[0].pageY + pointers[1].pageY);
          rotateStart.set(x, y);
        }
      }

      function handleTouchStartPan() {
        if (pointers.length === 1) {
          panStart.set(pointers[0].pageX, pointers[0].pageY);
        } else {
          var x = 0.5 * (pointers[0].pageX + pointers[1].pageX);
          var y = 0.5 * (pointers[0].pageY + pointers[1].pageY);
          panStart.set(x, y);
        }
      }

      function handleTouchStartDolly() {
        var dx = pointers[0].pageX - pointers[1].pageX;
        var dy = pointers[0].pageY - pointers[1].pageY;
        var distance = Math.sqrt(dx * dx + dy * dy);
        dollyStart.set(0, distance);
      }

      function handleTouchStartDollyPan() {
        if (scope.enableZoom) handleTouchStartDolly();
        if (scope.enablePan) handleTouchStartPan();
      }

      function handleTouchStartDollyRotate() {
        if (scope.enableZoom) handleTouchStartDolly();
        if (scope.enableRotate) handleTouchStartRotate();
      }

      function handleTouchMoveRotate(event) {
        if (pointers.length == 1) {
          rotateEnd.set(event.pageX, event.pageY);
        } else {
          var position = getSecondPointerPosition(event);
          var x = 0.5 * (event.pageX + position.x);
          var y = 0.5 * (event.pageY + position.y);
          rotateEnd.set(x, y);
        }

        rotateDelta.subVectors(rotateEnd, rotateStart).multiplyScalar(scope.rotateSpeed);
        var element = scope.domElement;
        rotateLeft(2 * Math.PI * rotateDelta.x / element.clientHeight); // yes, height

        rotateUp(2 * Math.PI * rotateDelta.y / element.clientHeight);
        rotateStart.copy(rotateEnd);
      }

      function handleTouchMovePan(event) {
        if (pointers.length === 1) {
          panEnd.set(event.pageX, event.pageY);
        } else {
          var position = getSecondPointerPosition(event);
          var x = 0.5 * (event.pageX + position.x);
          var y = 0.5 * (event.pageY + position.y);
          panEnd.set(x, y);
        }

        panDelta.subVectors(panEnd, panStart).multiplyScalar(scope.panSpeed);
        pan(panDelta.x, panDelta.y);
        panStart.copy(panEnd);
      }

      function handleTouchMoveDolly(event) {
        var position = getSecondPointerPosition(event);
        var dx = event.pageX - position.x;
        var dy = event.pageY - position.y;
        var distance = Math.sqrt(dx * dx + dy * dy);
        dollyEnd.set(0, distance);
        dollyDelta.set(0, Math.pow(dollyEnd.y / dollyStart.y, scope.zoomSpeed));
        dollyOut(dollyDelta.y);
        dollyStart.copy(dollyEnd);
      }

      function handleTouchMoveDollyPan(event) {
        if (scope.enableZoom) handleTouchMoveDolly(event);
        if (scope.enablePan) handleTouchMovePan(event);
      }

      function handleTouchMoveDollyRotate(event) {
        if (scope.enableZoom) handleTouchMoveDolly(event);
        if (scope.enableRotate) handleTouchMoveRotate(event);
      } //
      // event handlers - FSM: listen for events and reset state
      //


      function onPointerDown(event) {
        if (scope.enabled === false) return;

        if (pointers.length === 0) {
          scope.domElement.setPointerCapture(event.pointerId);
          scope.domElement.addEventListener("pointermove", onPointerMove);
          scope.domElement.addEventListener("pointerup", onPointerUp);
        } //


        addPointer(event);

        if (event.pointerType === "touch") {
          onTouchStart(event);
        } else {
          onMouseDown(event);
        }
      }

      function onPointerMove(event) {
        if (scope.enabled === false) return;

        if (event.pointerType === "touch") {
          onTouchMove(event);
        } else {
          onMouseMove(event);
        }
      }

      function onPointerUp(event) {
        removePointer(event);

        if (pointers.length === 0) {
          scope.domElement.releasePointerCapture(event.pointerId);
          scope.domElement.removeEventListener("pointermove", onPointerMove);
          scope.domElement.removeEventListener("pointerup", onPointerUp);
        }

        scope.dispatchEvent(_endEvent);
        state = STATE.NONE;
      }

      function onPointerCancel(event) {
        removePointer(event);
      }

      function onMouseDown(event) {
        var mouseAction;

        switch (event.button) {
          case 0:
            mouseAction = scope.mouseButtons.LEFT;
            break;

          case 1:
            mouseAction = scope.mouseButtons.MIDDLE;
            break;

          case 2:
            mouseAction = scope.mouseButtons.RIGHT;
            break;

          default:
            mouseAction = -1;
        }

        switch (mouseAction) {
          case THREE.MOUSE.DOLLY:
            if (scope.enableZoom === false) return;
            handleMouseDownDolly(event);
            state = STATE.DOLLY;
            break;

          case THREE.MOUSE.ROTATE:
            if (event.ctrlKey || event.metaKey || event.shiftKey) {
              if (scope.enablePan === false) return;
              handleMouseDownPan(event);
              state = STATE.PAN;
            } else {
              if (scope.enableRotate === false) return;
              handleMouseDownRotate(event);
              state = STATE.ROTATE;
            }

            break;

          case THREE.MOUSE.PAN:
            if (event.ctrlKey || event.metaKey || event.shiftKey) {
              if (scope.enableRotate === false) return;
              handleMouseDownRotate(event);
              state = STATE.ROTATE;
            } else {
              if (scope.enablePan === false) return;
              handleMouseDownPan(event);
              state = STATE.PAN;
            }

            break;

          default:
            state = STATE.NONE;
        }

        if (state !== STATE.NONE) {
          scope.dispatchEvent(_startEvent);
        }
      }

      function onMouseMove(event) {
        if (scope.enabled === false) return;

        switch (state) {
          case STATE.ROTATE:
            if (scope.enableRotate === false) return;
            handleMouseMoveRotate(event);
            break;

          case STATE.DOLLY:
            if (scope.enableZoom === false) return;
            handleMouseMoveDolly(event);
            break;

          case STATE.PAN:
            if (scope.enablePan === false) return;
            handleMouseMovePan(event);
            break;
        }
      }

      function onMouseWheel(event) {
        if (scope.enabled === false || scope.enableZoom === false || state !== STATE.NONE) return;
        event.preventDefault();
        scope.dispatchEvent(_startEvent);
        handleMouseWheel(event);
        scope.dispatchEvent(_endEvent);
      }

      function onKeyDown(event) {
        if (scope.enabled === false || scope.enablePan === false) return;
        handleKeyDown(event);
      }

      function onTouchStart(event) {
        trackPointer(event);

        switch (pointers.length) {
          case 1:
            switch (scope.touches.ONE) {
              case THREE.TOUCH.ROTATE:
                if (scope.enableRotate === false) return;
                handleTouchStartRotate();
                state = STATE.TOUCH_ROTATE;
                break;

              case THREE.TOUCH.PAN:
                if (scope.enablePan === false) return;
                handleTouchStartPan();
                state = STATE.TOUCH_PAN;
                break;

              default:
                state = STATE.NONE;
            }

            break;

          case 2:
            switch (scope.touches.TWO) {
              case THREE.TOUCH.DOLLY_PAN:
                if (scope.enableZoom === false && scope.enablePan === false) return;
                handleTouchStartDollyPan();
                state = STATE.TOUCH_DOLLY_PAN;
                break;

              case THREE.TOUCH.DOLLY_ROTATE:
                if (scope.enableZoom === false && scope.enableRotate === false) return;
                handleTouchStartDollyRotate();
                state = STATE.TOUCH_DOLLY_ROTATE;
                break;

              default:
                state = STATE.NONE;
            }

            break;

          default:
            state = STATE.NONE;
        }

        if (state !== STATE.NONE) {
          scope.dispatchEvent(_startEvent);
        }
      }

      function onTouchMove(event) {
        trackPointer(event);

        switch (state) {
          case STATE.TOUCH_ROTATE:
            if (scope.enableRotate === false) return;
            handleTouchMoveRotate(event);
            scope.update();
            break;

          case STATE.TOUCH_PAN:
            if (scope.enablePan === false) return;
            handleTouchMovePan(event);
            scope.update();
            break;

          case STATE.TOUCH_DOLLY_PAN:
            if (scope.enableZoom === false && scope.enablePan === false) return;
            handleTouchMoveDollyPan(event);
            scope.update();
            break;

          case STATE.TOUCH_DOLLY_ROTATE:
            if (scope.enableZoom === false && scope.enableRotate === false) return;
            handleTouchMoveDollyRotate(event);
            scope.update();
            break;

          default:
            state = STATE.NONE;
        }
      }

      function onContextMenu(event) {
        if (scope.enabled === false) return;
        event.preventDefault();
      }

      function addPointer(event) {
        pointers.push(event);
      }

      function removePointer(event) {
        delete pointerPositions[event.pointerId];

        for (var i = 0; i < pointers.length; i++) {
          if (pointers[i].pointerId == event.pointerId) {
            pointers.splice(i, 1);
            return;
          }
        }
      }

      function trackPointer(event) {
        var position = pointerPositions[event.pointerId];

        if (position === undefined) {
          position = new THREE.Vector2();
          pointerPositions[event.pointerId] = position;
        }

        position.set(event.pageX, event.pageY);
      }

      function getSecondPointerPosition(event) {
        var pointer = event.pointerId === pointers[0].pointerId ? pointers[1] : pointers[0];
        return pointerPositions[pointer.pointerId];
      } //


      scope.domElement.addEventListener("contextmenu", onContextMenu);
      scope.domElement.addEventListener("pointerdown", onPointerDown);
      scope.domElement.addEventListener("pointercancel", onPointerCancel);
      scope.domElement.addEventListener("wheel", onMouseWheel, {
        passive: false
      }); // force an update at start

      _this.update();

      return _this;
    }

    return _createClass(OrbitControls);
  }(THREE.EventDispatcher); // This set of controls performs orbiting, dollying (zooming), and panning.

  var FUEL_HOST = "fuel.gazebosim.org";
  var FUEL_VERSION = "1.0";
  var IGN_FUEL_HOST = "fuel.ignitionrobotics.org";
  /**
   * Create a valid URI that points to the Fuel Server given a local filesystem
   * path.
   *
   * A local filesystem path, such as
   * `/home/developer/.ignition/fuel/.../model/1/model.sdf` is typically found
   * when parsing object sent from a websocket server.
   *
   * The provided URI is returned if it does not point to the Fuel Server
   * directly.
   *
   * @param {string} uri - A string to convert to a Fuel Server URI, if able.
   * @return The transformed URI, or the same URI if it couldn't be transformed.
   */

  function createFuelUri(uri) {
    // Check if it's already a Fuel URI.
    if (uri.startsWith("https://".concat(FUEL_HOST)) || uri.startsWith("https://".concat(IGN_FUEL_HOST))) {
      return uri;
    } // Check to see if the uri has the form similar to
    // `/home/.../fuel.gazebosim.org/...`
    // If so, then we assume that the parts following
    // `fuel.gazebosim.org` can be directly mapped to a valid URL on
    // Fuel server.


    if (uri.indexOf(FUEL_HOST) > 0 || uri.indexOf(IGN_FUEL_HOST) > 0) {
      var uriArray = uri.split("/").filter(function (element) {
        return element !== "";
      });

      if (uri.indexOf(FUEL_HOST) > 0) {
        uriArray.splice(0, uriArray.indexOf(FUEL_HOST));
      } else {
        uriArray.splice(0, uriArray.indexOf(IGN_FUEL_HOST));
      }

      uriArray.splice(1, 0, FUEL_VERSION);
      uriArray.splice(6, 0, "files");
      return "https://" + uriArray.join("/");
    }

    return uri;
  }
  var FuelServer = /*#__PURE__*/function () {
    /**
     * FuelServer is in charge of making requests to the Fuel servers.
     * @param {string} host - The Server host url.
     * @param {string} version - The version used.
     **/
    function FuelServer() {
      _classCallCheck(this, FuelServer);

      this.requestHeader = {};
      this.host = FUEL_HOST;
      this.version = FUEL_VERSION;
      this.requestHeader = {};
    }
    /**
     * Get the list of files a model or world has.
     * @param {string} uri - The uri of the model or world.
     * @param {function} callback - The callback to use once the files are ready.
     */


    _createClass(FuelServer, [{
      key: "getFiles",
      value: function getFiles(uri, callback) {
        // Note: jshint is ignored as we use fetch API here instead of a XMLHttpRequest.
        // We still handle the response in a callback.
        // TODO(germanmas): We should update and use async/await instead throughout the library.
        var filesUrl = "".concat(uri.trim(), "/tip/files"); // Make the request to get the files.

        fetch(filesUrl, {
          headers: this.requestHeader
        }).then(function (res) {
          return res.json();
        }).then(function (json) {
          var files = prepareURLs(json["file_tree"], filesUrl);
          callback(files);
        })["catch"](function (error) {
          return console.error(error);
        }); // Helper function to parse the file tree of the response into an array of
        // file paths. The file tree from the Server consists of file elements
        // that contain a name, a path and children (if they are a folder).

        function prepareURLs(fileTree, baseUrl) {
          var parsedFiles = [];

          for (var i = 0; i < fileTree.length; i++) {
            // Avoid the thumbnails folder.
            if (fileTree[i].name === "thumbnails") {
              continue;
            } // Loop through files to extract files from folders.


            extractFile(fileTree[i]);
          }

          return parsedFiles; // Helper function to extract the files from the file tree.
          // Folder elements have children, while files don't.

          function extractFile(el) {
            if (!el.children) {
              // Avoid config files as they are not used.
              if (el.name.endsWith(".config")) {
                return;
              }

              var url = baseUrl + el.path;
              parsedFiles.push(url);
            } else {
              for (var j = 0; j < el.children.length; j++) {
                extractFile(el.children[j]);
              }
            }
          }
        }
      }
      /**
       * Set a request header for internal requests.
       *
       * @param {string} header - The header to send in the request.
       * @param {string} value - The value to set to the header.
       */

    }, {
      key: "setRequestHeader",
      value: function setRequestHeader(header, value) {
        this.requestHeader = _defineProperty({}, header, value);
      }
    }]);

    return FuelServer;
  }();

  var Pose = /*#__PURE__*/_createClass(function Pose(pos, rot) {
    _classCallCheck(this, Pose);

    this.position = new THREE.Vector3();
    this.orientation = new THREE.Quaternion();

    if (pos) {
      this.position = pos;
    }

    if (rot) {
      this.orientation = rot;
    }
  });

  /**
   * Spawn a model into the scene
   * @constructor
   */

  var SpawnModel = /*#__PURE__*/function () {
    function SpawnModel(scene, domElement) {
      _classCallCheck(this, SpawnModel);

      this.active = false;
      this.plane = new THREE__namespace.Plane(new THREE__namespace.Vector3(0, 0, 1), 0);
      this.ray = new THREE__namespace.Ray();
      this.snapDist = undefined;
      this.scene = scene;
      this.domElement = domElement !== undefined ? domElement : document; // Material for simple shapes being spawned (grey transparent)

      this.spawnedShapeMaterial = new THREE__namespace.MeshPhongMaterial({
        color: 0xffffff,
        flatShading: false
      });
      this.spawnedShapeMaterial.transparent = true;
      this.spawnedShapeMaterial.opacity = 0.5;
    }
    /**
     * Start spawning an entity. Only simple shapes supported so far.
     * Adds a temp object to the scene which is not registered on the server.
     * @param {string} entity
     * @param {function} callback
     */


    _createClass(SpawnModel, [{
      key: "start",
      value: function start(entity, callback) {
        if (this.active) {
          this.finish();
        }

        this.callback = callback;
        var that = this;

        function meshLoaded(mesh, spawnedMat) {
          if (spawnedMat) {
            mesh.material = that.spawnedShapeMaterial;
          }

          that.obj.name = that.generateUniqueName(entity);
          that.obj.add(mesh);
        }

        this.obj = new THREE__namespace.Object3D();

        if (entity === "box") {
          meshLoaded(this.scene.createBox(1, 1, 1), true);
        } else if (entity === "sphere") {
          meshLoaded(this.scene.createSphere(0.5), true);
        } else if (entity === "cylinder") {
          meshLoaded(this.scene.createCylinder(0.5, 1.0), true);
        } else if (entity === "capsule") {
          meshLoaded(this.scene.createCapsule(1, 1), true);
        } else if (entity === "pointlight") {
          meshLoaded(this.scene.createLight(1), false);
        } else if (entity === "spotlight") {
          meshLoaded(this.scene.createLight(2), false);
        } else if (entity === "directionallight") {
          meshLoaded(this.scene.createLight(3), false);
        } else {
          this.sdfParser.loadSDF(entity, meshLoaded); //TODO: add transparency to the object
        } // temp model appears within current view


        var pos = new THREE__namespace.Vector2(window.window.innerWidth / 2, window.innerHeight / 2);
        var intersect = new THREE__namespace.Vector3();
        this.scene.getRayCastModel(pos, intersect);
        this.obj.position.x = intersect.x;
        this.obj.position.y = intersect.y;
        this.obj.position.z += 0.5;
        this.scene.add(this.obj); // For the inserted light to have effect

        var allObjects = [];
        getDescendants(this.scene.scene, allObjects);

        for (var l = 0; l < allObjects.length; ++l) {
          if (allObjects[l].material) {
            allObjects[l].material.needsUpdate = true;
          }
        }
        /*this.mouseDown = function(event) {that.onMouseDown(event);};
        this.mouseUp = function(event) {that.onMouseUp(event);};
        this.mouseMove = function(event) {that.onMouseMove(event);};
        this.keyDown = function(event) {that.onKeyDown(event);};
        this.touchMove = function(event) {that.onTouchMove(event,true);};
        this.touchEnd = function(event) {that.onTouchEnd(event);};
               this.domElement.addEventListener('mousedown', that.mouseDown, false);
        this.domElement.addEventListener( 'mouseup', that.mouseUp, false);
        this.domElement.addEventListener( 'mousemove', that.mouseMove, false);
        document.addEventListener( 'keydown', that.keyDown, false);
               this.domElement.addEventListener( 'touchmove', that.touchMove, false);
        this.domElement.addEventListener( 'touchend', that.touchEnd, false);
        */


        this.active = true;
      }
      /**
       * Finish spawning an entity: re-enable camera controls,
       * remove listeners, remove temp object
       */

    }, {
      key: "finish",
      value: function finish() {
        /*this.domElement.removeEventListener( 'mousedown', that.mouseDown, false);
        this.domElement.removeEventListener( 'mouseup', that.mouseUp, false);
        this.domElement.removeEventListener( 'mousemove', that.mouseMove, false);
        document.removeEventListener( 'keydown', that.keyDown, false);
        */

        this.scene.remove(this.obj);
        this.active = false;
      }
      /**
       * Window event callback
       * @param {} event - not yet
       */

      /*public onMouseDown(event: MouseEvent): void {
        // Does this ever get called?
        // Change like this:
        // https://bitbucket.org/osrf/gzweb/pull-request/14
        event.preventDefault();
        event.stopImmediatePropagation();
      }*/

      /**
       * Window event callback
       * @param {} event - mousemove events
       */

      /*public onMouseMove(event: MouseEvent): void {
        if (!this.active) {
          return;
        }
      
        event.preventDefault();
      
        this.moveSpawnedModel(event.clientX,event.clientY);
      }*/

      /**
       * Window event callback
       * @param {} event - touchmove events
       */

      /*public onTouchMove(event: TouchEvent, originalEvent: any): void {
        if (!this.active) {
          return;
        }
      
        var e;
      
        if (originalEvent) {
          e = event;
        }
        else {
          e = event.originalEvent;
        }
        e.preventDefault();
      
        if (e.touches.length === 1) {
          this.moveSpawnedModel(e.touches[ 0 ].pageX,e.touches[ 0 ].pageY);
        }
      }*/

      /**
       * Window event callback
       * @param {} event - touchend events
       */

      /*public onTouchEnd = function(): void {
        if (!this.active) {
          return;
        }
      
        this.callback(this.obj);
        this.finish();
      }*/

      /**
       * Window event callback
       * @param {} event - mousedown events
       */

      /*public onMouseUp(event: MouseEvent): void {
        if (!this.active) {
          return;
        }
      
        this.callback(this.obj);
        this.finish();
      }*/

      /**
       * Window event callback
       * @param {} event - keydown events
       */

      /*public onKeyDown(event: KeyEvent): void {
        if ( event.keyCode === 27 ) // Esc
        {
          this.finish();
        }
      }*/

      /**
       * Move temp spawned model
       * @param {integer} positionX - Horizontal position on the canvas
       * @param {integer} positionY - Vertical position on the canvas
       */

      /*public moveSpawnedModel(positionX: number, positionY: number): void {
        var vector = new THREE.Vector3( (positionX / window.innerWidth) * 2 - 1,
              -(positionY / window.innerHeight) * 2 + 1, 0.5);
        vector.unproject(this.scene.camera);
        this.ray.set(this.scene.camera.position,
            vector.sub(this.scene.camera.position).normalize());
        var point = this.ray.intersectPlane(this.plane);
      
        if (!point)
        {
          return;
        }
      
        point.z = this.obj.position.z;
      
        if (this.snapDist) {
          point.x = Math.round(point.x / this.snapDist) * this.snapDist;
          point.y = Math.round(point.y / this.snapDist) * this.snapDist;
        }
      
        this.scene.setPose(this.obj, point, new THREE.Quaternion());
      
        if (this.obj.children[0].children[0] &&
           (this.obj.children[0].children[0] instanceof THREE.SpotLight ||
            this.obj.children[0].children[0] instanceof THREE.DirectionalLight))
        {
          var lightObj = this.obj.children[0].children[0];
          if (lightObj.direction)
          {
            if (lightObj.target)
            {
              lightObj.target.position.copy(lightObj.direction);
            }
          }
        }
      }*/

      /**
       * Generate unique name for spawned entity
       * @param {string} entity - entity type
       */

    }, {
      key: "generateUniqueName",
      value: function generateUniqueName(entity) {
        var i = 0;

        while (i < 1000) {
          if (this.scene.getByName(entity + "_" + i)) {
            ++i;
          } else {
            return entity + "_" + i;
          }
        }

        return entity;
      }
    }]);

    return SpawnModel;
  }();

  /**
   * Description: A THREE loader for STL ASCII files, as created by Solidworks and other CAD programs.
   *
   * Supports both binary and ASCII encoded files, with automatic detection of type.
   *
   * The loader returns a non-indexed buffer geometry.
   *
   * Limitations:
   *  Binary decoding supports "Magics" color format (http://en.wikipedia.org/wiki/STL_(file_format)#Color_in_binary_STL).
   *  There is perhaps some question as to how valid it is to always assume little-endian-ness.
   *  ASCII decoding assumes file is UTF-8.
   *
   * Usage:
   *  const loader = new STLLoader();
   *  loader.load( './models/stl/slotted_disk.stl', function ( geometry ) {
   *    scene.add( new THREE.Mesh( geometry ) );
   *  });
   *
   * For binary STLs geometry might contain colors for vertices. To use it:
   *  // use the same code to load STL as above
   *  if (geometry.hasColors) {
   *    material = new THREE.MeshPhongMaterial({ opacity: geometry.alpha, vertexColors: true });
   *  } else { .... }
   *  const mesh = new THREE.Mesh( geometry, material );
   *
   * For ASCII STLs containing multiple solids, each solid is assigned to a different group.
   * Groups can be used to assign a different color by defining an array of materials with the same length of
   * geometry.groups and passing it to the Mesh constructor:
   *
   * const mesh = new THREE.Mesh( geometry, material );
   *
   * For example:
   *
   *  const materials = [];
   *  const nGeometryGroups = geometry.groups.length;
   *
   *  const colorMap = ...; // Some logic to index colors.
   *
   *  for (let i = 0; i < nGeometryGroups; i++) {
   *
   *		const material = new THREE.MeshPhongMaterial({
   *			color: colorMap[i],
   *			wireframe: false
   *		});
   *
   *  }
   *
   *  materials.push(material);
   *  const mesh = new THREE.Mesh(geometry, materials);
   */

  var STLLoader = /*#__PURE__*/function (_Loader) {
    _inherits(STLLoader, _Loader);

    var _super = _createSuper(STLLoader);

    function STLLoader(manager) {
      _classCallCheck(this, STLLoader);

      return _super.call(this, manager);
    }

    _createClass(STLLoader, [{
      key: "load",
      value: function load(url, onLoad, onProgress, onError) {
        var scope = this;
        var loader = new THREE.FileLoader(this.manager);
        loader.setPath(this.path);
        loader.setResponseType("arraybuffer");
        loader.setRequestHeader(this.requestHeader);
        loader.setWithCredentials(this.withCredentials);
        loader.load(url, function (text) {
          try {
            onLoad(scope.parse(text));
          } catch (e) {
            if (onError) {
              onError(e);
            } else {
              console.error(e);
            }

            scope.manager.itemError(url);
          }
        }, onProgress, onError);
      }
    }, {
      key: "parse",
      value: function parse(data) {
        function isBinary(data) {
          var reader = new DataView(data.buffer, data.byteOffset);
          var face_size = 32 / 8 * 3 + 32 / 8 * 3 * 3 + 16 / 8;
          var n_faces = reader.getUint32(80, true);
          var expect = 80 + 32 / 8 + n_faces * face_size;

          if (expect === reader.byteLength) {
            return true;
          } // An ASCII STL data must begin with 'solid ' as the first six bytes.
          // However, ASCII STLs lacking the SPACE after the 'd' are known to be
          // plentiful.  So, check the first 5 bytes for 'solid'.
          // Several encodings, such as UTF-8, precede the text with up to 5 bytes:
          // https://en.wikipedia.org/wiki/Byte_order_mark#Byte_order_marks_by_encoding
          // Search for "solid" to start anywhere after those prefixes.
          // US-ASCII ordinal values for 's', 'o', 'l', 'i', 'd'


          var solid = [115, 111, 108, 105, 100];

          for (var off = 0; off < 5; off++) {
            // If "solid" text is matched to the current offset, declare it to be an ASCII STL.
            if (matchDataViewAt(solid, reader, off)) return false;
          } // Couldn't find "solid" text at the beginning; it is binary STL.


          return true;
        }

        function matchDataViewAt(query, reader, offset) {
          // Check if each byte in query matches the corresponding byte from the current offset
          for (var i = 0, il = query.length; i < il; i++) {
            if (query[i] !== reader.getUint8(offset + i)) return false;
          }

          return true;
        }

        function parseBinary(data) {
          var reader = new DataView(data.buffer, data.byteOffset);
          var faces = reader.getUint32(80, true);
          var r,
              g,
              b,
              hasColors = false,
              colors;
          var defaultR, defaultG, defaultB, alpha; // process STL header
          // check for default color in header ("COLOR=rgba" sequence).

          for (var index = 0; index < 80 - 10; index++) {
            if (reader.getUint32(index, false) == 0x434f4c4f
            /*COLO*/
            && reader.getUint8(index + 4) == 0x52
            /*'R'*/
            && reader.getUint8(index + 5) == 0x3d
            /*'='*/
            ) {
              hasColors = true;
              colors = new Float32Array(faces * 3 * 3);
              defaultR = reader.getUint8(index + 6) / 255;
              defaultG = reader.getUint8(index + 7) / 255;
              defaultB = reader.getUint8(index + 8) / 255;
              alpha = reader.getUint8(index + 9) / 255;
            }
          }

          var dataOffset = 84;
          var faceLength = 12 * 4 + 2;
          var geometry = new THREE.BufferGeometry();
          var vertices = new Float32Array(faces * 3 * 3);
          var normals = new Float32Array(faces * 3 * 3);

          for (var face = 0; face < faces; face++) {
            var start = dataOffset + face * faceLength;
            var normalX = reader.getFloat32(start, true);
            var normalY = reader.getFloat32(start + 4, true);
            var normalZ = reader.getFloat32(start + 8, true);

            if (hasColors) {
              var packedColor = reader.getUint16(start + 48, true);

              if ((packedColor & 0x8000) === 0) {
                // facet has its own unique color
                r = (packedColor & 0x1f) / 31;
                g = (packedColor >> 5 & 0x1f) / 31;
                b = (packedColor >> 10 & 0x1f) / 31;
              } else {
                r = defaultR;
                g = defaultG;
                b = defaultB;
              }
            }

            for (var i = 1; i <= 3; i++) {
              var vertexstart = start + i * 12;
              var componentIdx = face * 3 * 3 + (i - 1) * 3;
              vertices[componentIdx] = reader.getFloat32(vertexstart, true);
              vertices[componentIdx + 1] = reader.getFloat32(vertexstart + 4, true);
              vertices[componentIdx + 2] = reader.getFloat32(vertexstart + 8, true);
              normals[componentIdx] = normalX;
              normals[componentIdx + 1] = normalY;
              normals[componentIdx + 2] = normalZ;

              if (hasColors) {
                colors[componentIdx] = r;
                colors[componentIdx + 1] = g;
                colors[componentIdx + 2] = b;
              }
            }
          }

          geometry.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
          geometry.setAttribute("normal", new THREE.BufferAttribute(normals, 3));

          if (hasColors) {
            geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
            geometry.hasColors = true;
            geometry.alpha = alpha;
          }

          return geometry;
        }

        function parseASCII(data) {
          var geometry = new THREE.BufferGeometry();
          var patternSolid = /solid([\s\S]*?)endsolid/g;
          var patternFace = /facet([\s\S]*?)endfacet/g;
          var faceCounter = 0;
          var patternFloat = /[\s]+([+-]?(?:\d*)(?:\.\d*)?(?:[eE][+-]?\d+)?)/.source;
          var patternVertex = new RegExp("vertex" + patternFloat + patternFloat + patternFloat, "g");
          var patternNormal = new RegExp("normal" + patternFloat + patternFloat + patternFloat, "g");
          var vertices = [];
          var normals = [];
          var normal = new THREE.Vector3();
          var result;
          var groupCount = 0;
          var startVertex = 0;
          var endVertex = 0;

          while ((result = patternSolid.exec(data)) !== null) {
            startVertex = endVertex;
            var solid = result[0];

            while ((result = patternFace.exec(solid)) !== null) {
              var vertexCountPerFace = 0;
              var normalCountPerFace = 0;
              var text = result[0];

              while ((result = patternNormal.exec(text)) !== null) {
                normal.x = parseFloat(result[1]);
                normal.y = parseFloat(result[2]);
                normal.z = parseFloat(result[3]);
                normalCountPerFace++;
              }

              while ((result = patternVertex.exec(text)) !== null) {
                vertices.push(parseFloat(result[1]), parseFloat(result[2]), parseFloat(result[3]));
                normals.push(normal.x, normal.y, normal.z);
                vertexCountPerFace++;
                endVertex++;
              } // every face have to own ONE valid normal


              if (normalCountPerFace !== 1) {
                console.error("THREE.STLLoader: Something isn't right with the normal of face number " + faceCounter);
              } // each face have to own THREE valid vertices


              if (vertexCountPerFace !== 3) {
                console.error("THREE.STLLoader: Something isn't right with the vertices of face number " + faceCounter);
              }

              faceCounter++;
            }

            var start = startVertex;
            var count = endVertex - startVertex;
            geometry.addGroup(start, count, groupCount);
            groupCount++;
          }

          geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
          geometry.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
          return geometry;
        }

        function ensureString(buffer) {
          if (typeof buffer !== "string") {
            return THREE.LoaderUtils.decodeText(new Uint8Array(buffer));
          }

          return buffer;
        }

        function ensureBinary(buffer) {
          if (typeof buffer === "string") {
            var array_buffer = new Uint8Array(buffer.length);

            for (var i = 0; i < buffer.length; i++) {
              array_buffer[i] = buffer.charCodeAt(i) & 0xff; // implicitly assumes little-endian
            }

            return array_buffer.buffer || array_buffer;
          } else {
            return buffer;
          }
        } // start


        var binData = ensureBinary(data);
        return new THREE.Mesh(isBinary(binData) ? parseBinary(binData) : parseASCII(ensureString(data)));
      }
    }]);

    return STLLoader;
  }(THREE.Loader);

  var GLTFLoader = /*#__PURE__*/function (_Loader) {
    _inherits(GLTFLoader, _Loader);

    var _super = _createSuper(GLTFLoader);

    function GLTFLoader(manager) {
      var _this;

      _classCallCheck(this, GLTFLoader);

      _this = _super.call(this, manager);
      _this.dracoLoader = null;
      _this.ktx2Loader = null;
      _this.meshoptDecoder = null;
      _this.pluginCallbacks = [];

      _this.register(function (parser) {
        return new GLTFMaterialsClearcoatExtension(parser);
      });

      _this.register(function (parser) {
        return new GLTFTextureBasisUExtension(parser);
      });

      _this.register(function (parser) {
        return new GLTFTextureWebPExtension(parser);
      });

      _this.register(function (parser) {
        return new GLTFMaterialsSheenExtension(parser);
      });

      _this.register(function (parser) {
        return new GLTFMaterialsTransmissionExtension(parser);
      });

      _this.register(function (parser) {
        return new GLTFMaterialsVolumeExtension(parser);
      });

      _this.register(function (parser) {
        return new GLTFMaterialsIorExtension(parser);
      });

      _this.register(function (parser) {
        return new GLTFMaterialsEmissiveStrengthExtension(parser);
      });

      _this.register(function (parser) {
        return new GLTFMaterialsSpecularExtension(parser);
      });

      _this.register(function (parser) {
        return new GLTFMaterialsIridescenceExtension(parser);
      });

      _this.register(function (parser) {
        return new GLTFLightsExtension(parser);
      });

      _this.register(function (parser) {
        return new GLTFMeshoptCompression(parser);
      });

      return _this;
    }

    _createClass(GLTFLoader, [{
      key: "load",
      value: function load(url, onLoad, onProgress, onError) {
        var scope = this;
        var resourcePath;

        if (this.resourcePath !== '') {
          resourcePath = this.resourcePath;
        } else if (this.path !== '') {
          resourcePath = this.path;
        } else {
          resourcePath = THREE.LoaderUtils.extractUrlBase(url);
        } // Tells the LoadingManager to track an extra item, which resolves after
        // the model is fully loaded. This means the count of items loaded will
        // be incorrect, but ensures manager.onLoad() does not fire early.


        this.manager.itemStart(url);

        var _onError = function _onError(e) {
          if (onError) {
            onError(e);
          } else {
            console.error(e);
          }

          scope.manager.itemError(url);
          scope.manager.itemEnd(url);
        };

        var loader = new THREE.FileLoader(this.manager);
        loader.setPath(this.path);
        loader.setResponseType('arraybuffer');
        loader.setRequestHeader(this.requestHeader);
        loader.setWithCredentials(this.withCredentials);
        loader.load(url, function (data) {
          try {
            scope.parse(data, resourcePath, function (gltf) {
              onLoad(gltf);
              scope.manager.itemEnd(url);
            }, _onError);
          } catch (e) {
            _onError(e);
          }
        }, onProgress, _onError);
      }
    }, {
      key: "setDRACOLoader",
      value: function setDRACOLoader(dracoLoader) {
        this.dracoLoader = dracoLoader;
        return this;
      }
    }, {
      key: "setDDSLoader",
      value: function setDDSLoader() {
        throw new Error('THREE.GLTFLoader: "MSFT_texture_dds" no longer supported. Please update to "KHR_texture_basisu".');
      }
    }, {
      key: "setKTX2Loader",
      value: function setKTX2Loader(ktx2Loader) {
        this.ktx2Loader = ktx2Loader;
        return this;
      }
    }, {
      key: "setMeshoptDecoder",
      value: function setMeshoptDecoder(meshoptDecoder) {
        this.meshoptDecoder = meshoptDecoder;
        return this;
      }
    }, {
      key: "register",
      value: function register(callback) {
        if (this.pluginCallbacks.indexOf(callback) === -1) {
          this.pluginCallbacks.push(callback);
        }

        return this;
      }
    }, {
      key: "unregister",
      value: function unregister(callback) {
        if (this.pluginCallbacks.indexOf(callback) !== -1) {
          this.pluginCallbacks.splice(this.pluginCallbacks.indexOf(callback), 1);
        }

        return this;
      }
    }, {
      key: "parse",
      value: function parse(data, path, onLoad, onError) {
        var content;
        var extensions = {};
        var plugins = {};

        if (typeof data === 'string') {
          content = data;
        } else {
          var magic = THREE.LoaderUtils.decodeText(new Uint8Array(data, 0, 4));

          if (magic === BINARY_EXTENSION_HEADER_MAGIC) {
            try {
              extensions[EXTENSIONS.KHR_BINARY_GLTF] = new GLTFBinaryExtension(data);
            } catch (error) {
              if (onError) onError(error);
              return;
            }

            content = extensions[EXTENSIONS.KHR_BINARY_GLTF].content;
          } else {
            content = THREE.LoaderUtils.decodeText(new Uint8Array(data));
          }
        }

        var json = JSON.parse(content);

        if (json.asset === undefined || json.asset.version[0] < 2) {
          if (onError) onError(new Error('THREE.GLTFLoader: Unsupported asset. glTF versions >=2.0 are supported.'));
          return;
        }

        var parser = new GLTFParser(json, {
          path: path || this.resourcePath || '',
          crossOrigin: this.crossOrigin,
          requestHeader: this.requestHeader,
          manager: this.manager,
          ktx2Loader: this.ktx2Loader,
          meshoptDecoder: this.meshoptDecoder
        });
        parser.fileLoader.setRequestHeader(this.requestHeader);

        for (var i = 0; i < this.pluginCallbacks.length; i++) {
          var plugin = this.pluginCallbacks[i](parser);
          plugins[plugin.name] = plugin; // Workaround to avoid determining as unknown extension
          // in addUnknownExtensionsToUserData().
          // Remove this workaround if we move all the existing
          // extension handlers to plugin system

          extensions[plugin.name] = true;
        }

        if (json.extensionsUsed) {
          for (var _i = 0; _i < json.extensionsUsed.length; ++_i) {
            var extensionName = json.extensionsUsed[_i];
            var extensionsRequired = json.extensionsRequired || [];

            switch (extensionName) {
              case EXTENSIONS.KHR_MATERIALS_UNLIT:
                extensions[extensionName] = new GLTFMaterialsUnlitExtension();
                break;

              case EXTENSIONS.KHR_MATERIALS_PBR_SPECULAR_GLOSSINESS:
                extensions[extensionName] = new GLTFMaterialsPbrSpecularGlossinessExtension();
                break;

              case EXTENSIONS.KHR_DRACO_MESH_COMPRESSION:
                extensions[extensionName] = new GLTFDracoMeshCompressionExtension(json, this.dracoLoader);
                break;

              case EXTENSIONS.KHR_TEXTURE_TRANSFORM:
                extensions[extensionName] = new GLTFTextureTransformExtension();
                break;

              case EXTENSIONS.KHR_MESH_QUANTIZATION:
                extensions[extensionName] = new GLTFMeshQuantizationExtension();
                break;

              default:
                if (extensionsRequired.indexOf(extensionName) >= 0 && plugins[extensionName] === undefined) {
                  console.warn('THREE.GLTFLoader: Unknown extension "' + extensionName + '".');
                }

            }
          }
        }

        parser.setExtensions(extensions);
        parser.setPlugins(plugins);
        parser.parse(onLoad, onError);
      }
    }, {
      key: "parseAsync",
      value: function parseAsync(data, path) {
        var scope = this;
        return new Promise(function (resolve, reject) {
          scope.parse(data, path, resolve, reject);
        });
      }
    }]);

    return GLTFLoader;
  }(THREE.Loader);
  /* GLTFREGISTRY */


  function GLTFRegistry() {
    var objects = {};
    return {
      get: function get(key) {
        return objects[key];
      },
      add: function add(key, object) {
        objects[key] = object;
      },
      remove: function remove(key) {
        delete objects[key];
      },
      removeAll: function removeAll() {
        objects = {};
      }
    };
  }
  /*********************************/

  /********** EXTENSIONS ***********/

  /*********************************/


  var EXTENSIONS = {
    KHR_BINARY_GLTF: 'KHR_binary_glTF',
    KHR_DRACO_MESH_COMPRESSION: 'KHR_draco_mesh_compression',
    KHR_LIGHTS_PUNCTUAL: 'KHR_lights_punctual',
    KHR_MATERIALS_CLEARCOAT: 'KHR_materials_clearcoat',
    KHR_MATERIALS_IOR: 'KHR_materials_ior',
    KHR_MATERIALS_PBR_SPECULAR_GLOSSINESS: 'KHR_materials_pbrSpecularGlossiness',
    KHR_MATERIALS_SHEEN: 'KHR_materials_sheen',
    KHR_MATERIALS_SPECULAR: 'KHR_materials_specular',
    KHR_MATERIALS_TRANSMISSION: 'KHR_materials_transmission',
    KHR_MATERIALS_IRIDESCENCE: 'KHR_materials_iridescence',
    KHR_MATERIALS_UNLIT: 'KHR_materials_unlit',
    KHR_MATERIALS_VOLUME: 'KHR_materials_volume',
    KHR_TEXTURE_BASISU: 'KHR_texture_basisu',
    KHR_TEXTURE_TRANSFORM: 'KHR_texture_transform',
    KHR_MESH_QUANTIZATION: 'KHR_mesh_quantization',
    KHR_MATERIALS_EMISSIVE_STRENGTH: 'KHR_materials_emissive_strength',
    EXT_TEXTURE_WEBP: 'EXT_texture_webp',
    EXT_MESHOPT_COMPRESSION: 'EXT_meshopt_compression'
  };
  /**
   * Punctual Lights Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Khronos/KHR_lights_punctual
   */

  var GLTFLightsExtension = /*#__PURE__*/function () {
    function GLTFLightsExtension(parser) {
      _classCallCheck(this, GLTFLightsExtension);

      this.parser = parser;
      this.name = EXTENSIONS.KHR_LIGHTS_PUNCTUAL; // Object3D instance caches

      this.cache = {
        refs: {},
        uses: {}
      };
    }

    _createClass(GLTFLightsExtension, [{
      key: "_markDefs",
      value: function _markDefs() {
        var parser = this.parser;
        var nodeDefs = this.parser.json.nodes || [];

        for (var nodeIndex = 0, nodeLength = nodeDefs.length; nodeIndex < nodeLength; nodeIndex++) {
          var nodeDef = nodeDefs[nodeIndex];

          if (nodeDef.extensions && nodeDef.extensions[this.name] && nodeDef.extensions[this.name].light !== undefined) {
            parser._addNodeRef(this.cache, nodeDef.extensions[this.name].light);
          }
        }
      }
    }, {
      key: "_loadLight",
      value: function _loadLight(lightIndex) {
        var parser = this.parser;
        var cacheKey = 'light:' + lightIndex;
        var dependency = parser.cache.get(cacheKey);
        if (dependency) return dependency;
        var json = parser.json;
        var extensions = json.extensions && json.extensions[this.name] || {};
        var lightDefs = extensions.lights || [];
        var lightDef = lightDefs[lightIndex];
        var lightNode;
        var color = new THREE.Color(0xffffff);
        if (lightDef.color !== undefined) color.fromArray(lightDef.color);
        var range = lightDef.range !== undefined ? lightDef.range : 0;

        switch (lightDef.type) {
          case 'directional':
            lightNode = new THREE.DirectionalLight(color);
            lightNode.target.position.set(0, 0, -1);
            lightNode.add(lightNode.target);
            break;

          case 'point':
            lightNode = new THREE.PointLight(color);
            lightNode.distance = range;
            break;

          case 'spot':
            lightNode = new THREE.SpotLight(color);
            lightNode.distance = range; // Handle spotlight properties.

            lightDef.spot = lightDef.spot || {};
            lightDef.spot.innerConeAngle = lightDef.spot.innerConeAngle !== undefined ? lightDef.spot.innerConeAngle : 0;
            lightDef.spot.outerConeAngle = lightDef.spot.outerConeAngle !== undefined ? lightDef.spot.outerConeAngle : Math.PI / 4.0;
            lightNode.angle = lightDef.spot.outerConeAngle;
            lightNode.penumbra = 1.0 - lightDef.spot.innerConeAngle / lightDef.spot.outerConeAngle;
            lightNode.target.position.set(0, 0, -1);
            lightNode.add(lightNode.target);
            break;

          default:
            throw new Error('THREE.GLTFLoader: Unexpected light type: ' + lightDef.type);
        } // Some lights (e.g. spot) default to a position other than the origin. Reset the position
        // here, because node-level parsing will only override position if explicitly specified.


        lightNode.position.set(0, 0, 0);
        lightNode.decay = 2;
        if (lightDef.intensity !== undefined) lightNode.intensity = lightDef.intensity;
        lightNode.name = parser.createUniqueName(lightDef.name || 'light_' + lightIndex);
        dependency = Promise.resolve(lightNode);
        parser.cache.add(cacheKey, dependency);
        return dependency;
      }
    }, {
      key: "createNodeAttachment",
      value: function createNodeAttachment(nodeIndex) {
        var self = this;
        var parser = this.parser;
        var json = parser.json;
        var nodeDef = json.nodes[nodeIndex];
        var lightDef = nodeDef.extensions && nodeDef.extensions[this.name] || {};
        var lightIndex = lightDef.light;
        if (lightIndex === undefined) return null;
        return this._loadLight(lightIndex).then(function (light) {
          return parser._getNodeRef(self.cache, lightIndex, light);
        });
      }
    }]);

    return GLTFLightsExtension;
  }();
  /**
   * Unlit Materials Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Khronos/KHR_materials_unlit
   */


  var GLTFMaterialsUnlitExtension = /*#__PURE__*/function () {
    function GLTFMaterialsUnlitExtension() {
      _classCallCheck(this, GLTFMaterialsUnlitExtension);

      this.name = EXTENSIONS.KHR_MATERIALS_UNLIT;
    }

    _createClass(GLTFMaterialsUnlitExtension, [{
      key: "getMaterialType",
      value: function getMaterialType() {
        return THREE.MeshBasicMaterial;
      }
    }, {
      key: "extendParams",
      value: function extendParams(materialParams, materialDef, parser) {
        var pending = [];
        materialParams.color = new THREE.Color(1.0, 1.0, 1.0);
        materialParams.opacity = 1.0;
        var metallicRoughness = materialDef.pbrMetallicRoughness;

        if (metallicRoughness) {
          if (Array.isArray(metallicRoughness.baseColorFactor)) {
            var array = metallicRoughness.baseColorFactor;
            materialParams.color.fromArray(array);
            materialParams.opacity = array[3];
          }

          if (metallicRoughness.baseColorTexture !== undefined) {
            pending.push(parser.assignTexture(materialParams, 'map', metallicRoughness.baseColorTexture, THREE.sRGBEncoding));
          }
        }

        return Promise.all(pending);
      }
    }]);

    return GLTFMaterialsUnlitExtension;
  }();
  /**
   * Materials Emissive Strength Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/blob/5768b3ce0ef32bc39cdf1bef10b948586635ead3/extensions/2.0/Khronos/KHR_materials_emissive_strength/README.md
   */


  var GLTFMaterialsEmissiveStrengthExtension = /*#__PURE__*/function () {
    function GLTFMaterialsEmissiveStrengthExtension(parser) {
      _classCallCheck(this, GLTFMaterialsEmissiveStrengthExtension);

      this.parser = parser;
      this.name = EXTENSIONS.KHR_MATERIALS_EMISSIVE_STRENGTH;
    }

    _createClass(GLTFMaterialsEmissiveStrengthExtension, [{
      key: "extendMaterialParams",
      value: function extendMaterialParams(materialIndex, materialParams) {
        var parser = this.parser;
        var materialDef = parser.json.materials[materialIndex];

        if (!materialDef.extensions || !materialDef.extensions[this.name]) {
          return Promise.resolve();
        }

        var emissiveStrength = materialDef.extensions[this.name].emissiveStrength;

        if (emissiveStrength !== undefined) {
          materialParams.emissiveIntensity = emissiveStrength;
        }

        return Promise.resolve();
      }
    }]);

    return GLTFMaterialsEmissiveStrengthExtension;
  }();
  /**
   * Clearcoat Materials Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Khronos/KHR_materials_clearcoat
   */


  var GLTFMaterialsClearcoatExtension = /*#__PURE__*/function () {
    function GLTFMaterialsClearcoatExtension(parser) {
      _classCallCheck(this, GLTFMaterialsClearcoatExtension);

      this.parser = parser;
      this.name = EXTENSIONS.KHR_MATERIALS_CLEARCOAT;
    }

    _createClass(GLTFMaterialsClearcoatExtension, [{
      key: "getMaterialType",
      value: function getMaterialType(materialIndex) {
        var parser = this.parser;
        var materialDef = parser.json.materials[materialIndex];
        if (!materialDef.extensions || !materialDef.extensions[this.name]) return null;
        return THREE.MeshPhysicalMaterial;
      }
    }, {
      key: "extendMaterialParams",
      value: function extendMaterialParams(materialIndex, materialParams) {
        var parser = this.parser;
        var materialDef = parser.json.materials[materialIndex];

        if (!materialDef.extensions || !materialDef.extensions[this.name]) {
          return Promise.resolve();
        }

        var pending = [];
        var extension = materialDef.extensions[this.name];

        if (extension.clearcoatFactor !== undefined) {
          materialParams.clearcoat = extension.clearcoatFactor;
        }

        if (extension.clearcoatTexture !== undefined) {
          pending.push(parser.assignTexture(materialParams, 'clearcoatMap', extension.clearcoatTexture));
        }

        if (extension.clearcoatRoughnessFactor !== undefined) {
          materialParams.clearcoatRoughness = extension.clearcoatRoughnessFactor;
        }

        if (extension.clearcoatRoughnessTexture !== undefined) {
          pending.push(parser.assignTexture(materialParams, 'clearcoatRoughnessMap', extension.clearcoatRoughnessTexture));
        }

        if (extension.clearcoatNormalTexture !== undefined) {
          pending.push(parser.assignTexture(materialParams, 'clearcoatNormalMap', extension.clearcoatNormalTexture));

          if (extension.clearcoatNormalTexture.scale !== undefined) {
            var scale = extension.clearcoatNormalTexture.scale;
            materialParams.clearcoatNormalScale = new THREE.Vector2(scale, scale);
          }
        }

        return Promise.all(pending);
      }
    }]);

    return GLTFMaterialsClearcoatExtension;
  }();
  /**
   * Iridescence Materials Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Khronos/KHR_materials_iridescence
   */


  var GLTFMaterialsIridescenceExtension = /*#__PURE__*/function () {
    function GLTFMaterialsIridescenceExtension(parser) {
      _classCallCheck(this, GLTFMaterialsIridescenceExtension);

      this.parser = parser;
      this.name = EXTENSIONS.KHR_MATERIALS_IRIDESCENCE;
    }

    _createClass(GLTFMaterialsIridescenceExtension, [{
      key: "getMaterialType",
      value: function getMaterialType(materialIndex) {
        var parser = this.parser;
        var materialDef = parser.json.materials[materialIndex];
        if (!materialDef.extensions || !materialDef.extensions[this.name]) return null;
        return THREE.MeshPhysicalMaterial;
      }
    }, {
      key: "extendMaterialParams",
      value: function extendMaterialParams(materialIndex, materialParams) {
        var parser = this.parser;
        var materialDef = parser.json.materials[materialIndex];

        if (!materialDef.extensions || !materialDef.extensions[this.name]) {
          return Promise.resolve();
        }

        var pending = [];
        var extension = materialDef.extensions[this.name];

        if (extension.iridescenceFactor !== undefined) {
          materialParams.iridescence = extension.iridescenceFactor;
        }

        if (extension.iridescenceTexture !== undefined) {
          pending.push(parser.assignTexture(materialParams, 'iridescenceMap', extension.iridescenceTexture));
        }

        if (extension.iridescenceIor !== undefined) {
          materialParams.iridescenceIOR = extension.iridescenceIor;
        }

        if (materialParams.iridescenceThicknessRange === undefined) {
          materialParams.iridescenceThicknessRange = [100, 400];
        }

        if (extension.iridescenceThicknessMinimum !== undefined) {
          materialParams.iridescenceThicknessRange[0] = extension.iridescenceThicknessMinimum;
        }

        if (extension.iridescenceThicknessMaximum !== undefined) {
          materialParams.iridescenceThicknessRange[1] = extension.iridescenceThicknessMaximum;
        }

        if (extension.iridescenceThicknessTexture !== undefined) {
          pending.push(parser.assignTexture(materialParams, 'iridescenceThicknessMap', extension.iridescenceThicknessTexture));
        }

        return Promise.all(pending);
      }
    }]);

    return GLTFMaterialsIridescenceExtension;
  }();
  /**
   * Sheen Materials Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Khronos/KHR_materials_sheen
   */


  var GLTFMaterialsSheenExtension = /*#__PURE__*/function () {
    function GLTFMaterialsSheenExtension(parser) {
      _classCallCheck(this, GLTFMaterialsSheenExtension);

      this.parser = parser;
      this.name = EXTENSIONS.KHR_MATERIALS_SHEEN;
    }

    _createClass(GLTFMaterialsSheenExtension, [{
      key: "getMaterialType",
      value: function getMaterialType(materialIndex) {
        var parser = this.parser;
        var materialDef = parser.json.materials[materialIndex];
        if (!materialDef.extensions || !materialDef.extensions[this.name]) return null;
        return THREE.MeshPhysicalMaterial;
      }
    }, {
      key: "extendMaterialParams",
      value: function extendMaterialParams(materialIndex, materialParams) {
        var parser = this.parser;
        var materialDef = parser.json.materials[materialIndex];

        if (!materialDef.extensions || !materialDef.extensions[this.name]) {
          return Promise.resolve();
        }

        var pending = [];
        materialParams.sheenColor = new THREE.Color(0, 0, 0);
        materialParams.sheenRoughness = 0;
        materialParams.sheen = 1;
        var extension = materialDef.extensions[this.name];

        if (extension.sheenColorFactor !== undefined) {
          materialParams.sheenColor.fromArray(extension.sheenColorFactor);
        }

        if (extension.sheenRoughnessFactor !== undefined) {
          materialParams.sheenRoughness = extension.sheenRoughnessFactor;
        }

        if (extension.sheenColorTexture !== undefined) {
          pending.push(parser.assignTexture(materialParams, 'sheenColorMap', extension.sheenColorTexture, THREE.sRGBEncoding));
        }

        if (extension.sheenRoughnessTexture !== undefined) {
          pending.push(parser.assignTexture(materialParams, 'sheenRoughnessMap', extension.sheenRoughnessTexture));
        }

        return Promise.all(pending);
      }
    }]);

    return GLTFMaterialsSheenExtension;
  }();
  /**
   * Transmission Materials Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Khronos/KHR_materials_transmission
   * Draft: https://github.com/KhronosGroup/glTF/pull/1698
   */


  var GLTFMaterialsTransmissionExtension = /*#__PURE__*/function () {
    function GLTFMaterialsTransmissionExtension(parser) {
      _classCallCheck(this, GLTFMaterialsTransmissionExtension);

      this.parser = parser;
      this.name = EXTENSIONS.KHR_MATERIALS_TRANSMISSION;
    }

    _createClass(GLTFMaterialsTransmissionExtension, [{
      key: "getMaterialType",
      value: function getMaterialType(materialIndex) {
        var parser = this.parser;
        var materialDef = parser.json.materials[materialIndex];
        if (!materialDef.extensions || !materialDef.extensions[this.name]) return null;
        return THREE.MeshPhysicalMaterial;
      }
    }, {
      key: "extendMaterialParams",
      value: function extendMaterialParams(materialIndex, materialParams) {
        var parser = this.parser;
        var materialDef = parser.json.materials[materialIndex];

        if (!materialDef.extensions || !materialDef.extensions[this.name]) {
          return Promise.resolve();
        }

        var pending = [];
        var extension = materialDef.extensions[this.name];

        if (extension.transmissionFactor !== undefined) {
          materialParams.transmission = extension.transmissionFactor;
        }

        if (extension.transmissionTexture !== undefined) {
          pending.push(parser.assignTexture(materialParams, 'transmissionMap', extension.transmissionTexture));
        }

        return Promise.all(pending);
      }
    }]);

    return GLTFMaterialsTransmissionExtension;
  }();
  /**
   * Materials Volume Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Khronos/KHR_materials_volume
   */


  var GLTFMaterialsVolumeExtension = /*#__PURE__*/function () {
    function GLTFMaterialsVolumeExtension(parser) {
      _classCallCheck(this, GLTFMaterialsVolumeExtension);

      this.parser = parser;
      this.name = EXTENSIONS.KHR_MATERIALS_VOLUME;
    }

    _createClass(GLTFMaterialsVolumeExtension, [{
      key: "getMaterialType",
      value: function getMaterialType(materialIndex) {
        var parser = this.parser;
        var materialDef = parser.json.materials[materialIndex];
        if (!materialDef.extensions || !materialDef.extensions[this.name]) return null;
        return THREE.MeshPhysicalMaterial;
      }
    }, {
      key: "extendMaterialParams",
      value: function extendMaterialParams(materialIndex, materialParams) {
        var parser = this.parser;
        var materialDef = parser.json.materials[materialIndex];

        if (!materialDef.extensions || !materialDef.extensions[this.name]) {
          return Promise.resolve();
        }

        var pending = [];
        var extension = materialDef.extensions[this.name];
        materialParams.thickness = extension.thicknessFactor !== undefined ? extension.thicknessFactor : 0;

        if (extension.thicknessTexture !== undefined) {
          pending.push(parser.assignTexture(materialParams, 'thicknessMap', extension.thicknessTexture));
        }

        materialParams.attenuationDistance = extension.attenuationDistance || 0;
        var colorArray = extension.attenuationColor || [1, 1, 1];
        materialParams.attenuationColor = new THREE.Color(colorArray[0], colorArray[1], colorArray[2]);
        return Promise.all(pending);
      }
    }]);

    return GLTFMaterialsVolumeExtension;
  }();
  /**
   * Materials ior Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Khronos/KHR_materials_ior
   */


  var GLTFMaterialsIorExtension = /*#__PURE__*/function () {
    function GLTFMaterialsIorExtension(parser) {
      _classCallCheck(this, GLTFMaterialsIorExtension);

      this.parser = parser;
      this.name = EXTENSIONS.KHR_MATERIALS_IOR;
    }

    _createClass(GLTFMaterialsIorExtension, [{
      key: "getMaterialType",
      value: function getMaterialType(materialIndex) {
        var parser = this.parser;
        var materialDef = parser.json.materials[materialIndex];
        if (!materialDef.extensions || !materialDef.extensions[this.name]) return null;
        return THREE.MeshPhysicalMaterial;
      }
    }, {
      key: "extendMaterialParams",
      value: function extendMaterialParams(materialIndex, materialParams) {
        var parser = this.parser;
        var materialDef = parser.json.materials[materialIndex];

        if (!materialDef.extensions || !materialDef.extensions[this.name]) {
          return Promise.resolve();
        }

        var extension = materialDef.extensions[this.name];
        materialParams.ior = extension.ior !== undefined ? extension.ior : 1.5;
        return Promise.resolve();
      }
    }]);

    return GLTFMaterialsIorExtension;
  }();
  /**
   * Materials specular Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Khronos/KHR_materials_specular
   */


  var GLTFMaterialsSpecularExtension = /*#__PURE__*/function () {
    function GLTFMaterialsSpecularExtension(parser) {
      _classCallCheck(this, GLTFMaterialsSpecularExtension);

      this.parser = parser;
      this.name = EXTENSIONS.KHR_MATERIALS_SPECULAR;
    }

    _createClass(GLTFMaterialsSpecularExtension, [{
      key: "getMaterialType",
      value: function getMaterialType(materialIndex) {
        var parser = this.parser;
        var materialDef = parser.json.materials[materialIndex];
        if (!materialDef.extensions || !materialDef.extensions[this.name]) return null;
        return THREE.MeshPhysicalMaterial;
      }
    }, {
      key: "extendMaterialParams",
      value: function extendMaterialParams(materialIndex, materialParams) {
        var parser = this.parser;
        var materialDef = parser.json.materials[materialIndex];

        if (!materialDef.extensions || !materialDef.extensions[this.name]) {
          return Promise.resolve();
        }

        var pending = [];
        var extension = materialDef.extensions[this.name];
        materialParams.specularIntensity = extension.specularFactor !== undefined ? extension.specularFactor : 1.0;

        if (extension.specularTexture !== undefined) {
          pending.push(parser.assignTexture(materialParams, 'specularIntensityMap', extension.specularTexture));
        }

        var colorArray = extension.specularColorFactor || [1, 1, 1];
        materialParams.specularColor = new THREE.Color(colorArray[0], colorArray[1], colorArray[2]);

        if (extension.specularColorTexture !== undefined) {
          pending.push(parser.assignTexture(materialParams, 'specularColorMap', extension.specularColorTexture, THREE.sRGBEncoding));
        }

        return Promise.all(pending);
      }
    }]);

    return GLTFMaterialsSpecularExtension;
  }();
  /**
   * BasisU Texture Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Khronos/KHR_texture_basisu
   */


  var GLTFTextureBasisUExtension = /*#__PURE__*/function () {
    function GLTFTextureBasisUExtension(parser) {
      _classCallCheck(this, GLTFTextureBasisUExtension);

      this.parser = parser;
      this.name = EXTENSIONS.KHR_TEXTURE_BASISU;
    }

    _createClass(GLTFTextureBasisUExtension, [{
      key: "loadTexture",
      value: function loadTexture(textureIndex) {
        var parser = this.parser;
        var json = parser.json;
        var textureDef = json.textures[textureIndex];

        if (!textureDef.extensions || !textureDef.extensions[this.name]) {
          return null;
        }

        var extension = textureDef.extensions[this.name];
        var loader = parser.options.ktx2Loader;

        if (!loader) {
          if (json.extensionsRequired && json.extensionsRequired.indexOf(this.name) >= 0) {
            throw new Error('THREE.GLTFLoader: setKTX2Loader must be called before loading KTX2 textures');
          } else {
            // Assumes that the extension is optional and that a fallback texture is present
            return null;
          }
        }

        return parser.loadTextureImage(textureIndex, extension.source, loader);
      }
    }]);

    return GLTFTextureBasisUExtension;
  }();
  /**
   * WebP Texture Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Vendor/EXT_texture_webp
   */


  var GLTFTextureWebPExtension = /*#__PURE__*/function () {
    function GLTFTextureWebPExtension(parser) {
      _classCallCheck(this, GLTFTextureWebPExtension);

      this.parser = parser;
      this.name = EXTENSIONS.EXT_TEXTURE_WEBP;
      this.isSupported = null;
    }

    _createClass(GLTFTextureWebPExtension, [{
      key: "loadTexture",
      value: function loadTexture(textureIndex) {
        var name = this.name;
        var parser = this.parser;
        var json = parser.json;
        var textureDef = json.textures[textureIndex];

        if (!textureDef.extensions || !textureDef.extensions[name]) {
          return null;
        }

        var extension = textureDef.extensions[name];
        var source = json.images[extension.source];
        var loader = parser.textureLoader;

        if (source.uri) {
          var handler = parser.options.manager.getHandler(source.uri);
          if (handler !== null) loader = handler;
        }

        return this.detectSupport().then(function (isSupported) {
          if (isSupported) return parser.loadTextureImage(textureIndex, extension.source, loader);

          if (json.extensionsRequired && json.extensionsRequired.indexOf(name) >= 0) {
            throw new Error('THREE.GLTFLoader: WebP required by asset but unsupported.');
          } // Fall back to PNG or JPEG.


          return parser.loadTexture(textureIndex);
        });
      }
    }, {
      key: "detectSupport",
      value: function detectSupport() {
        if (!this.isSupported) {
          this.isSupported = new Promise(function (resolve) {
            var image = new Image(); // Lossy test image. Support for lossy images doesn't guarantee support for all
            // WebP images, unfortunately.

            image.src = 'data:image/webp;base64,UklGRiIAAABXRUJQVlA4IBYAAAAwAQCdASoBAAEADsD+JaQAA3AAAAAA';

            image.onload = image.onerror = function () {
              resolve(image.height === 1);
            };
          });
        }

        return this.isSupported;
      }
    }]);

    return GLTFTextureWebPExtension;
  }();
  /**
   * meshopt BufferView Compression Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Vendor/EXT_meshopt_compression
   */


  var GLTFMeshoptCompression = /*#__PURE__*/function () {
    function GLTFMeshoptCompression(parser) {
      _classCallCheck(this, GLTFMeshoptCompression);

      this.name = EXTENSIONS.EXT_MESHOPT_COMPRESSION;
      this.parser = parser;
    }

    _createClass(GLTFMeshoptCompression, [{
      key: "loadBufferView",
      value: function loadBufferView(index) {
        var json = this.parser.json;
        var bufferView = json.bufferViews[index];

        if (bufferView.extensions && bufferView.extensions[this.name]) {
          var extensionDef = bufferView.extensions[this.name];
          var buffer = this.parser.getDependency('buffer', extensionDef.buffer);
          var decoder = this.parser.options.meshoptDecoder;

          if (!decoder || !decoder.supported) {
            if (json.extensionsRequired && json.extensionsRequired.indexOf(this.name) >= 0) {
              throw new Error('THREE.GLTFLoader: setMeshoptDecoder must be called before loading compressed files');
            } else {
              // Assumes that the extension is optional and that fallback buffer data is present
              return null;
            }
          }

          return Promise.all([buffer, decoder.ready]).then(function (res) {
            var byteOffset = extensionDef.byteOffset || 0;
            var byteLength = extensionDef.byteLength || 0;
            var count = extensionDef.count;
            var stride = extensionDef.byteStride;
            var result = new ArrayBuffer(count * stride);
            var source = new Uint8Array(res[0], byteOffset, byteLength);
            decoder.decodeGltfBuffer(new Uint8Array(result), count, stride, source, extensionDef.mode, extensionDef.filter);
            return result;
          });
        } else {
          return null;
        }
      }
    }]);

    return GLTFMeshoptCompression;
  }();
  /* BINARY EXTENSION */


  var BINARY_EXTENSION_HEADER_MAGIC = 'glTF';
  var BINARY_EXTENSION_HEADER_LENGTH = 12;
  var BINARY_EXTENSION_CHUNK_TYPES = {
    JSON: 0x4E4F534A,
    BIN: 0x004E4942
  };

  var GLTFBinaryExtension = /*#__PURE__*/_createClass(function GLTFBinaryExtension(data) {
    _classCallCheck(this, GLTFBinaryExtension);

    this.name = EXTENSIONS.KHR_BINARY_GLTF;
    this.content = null;
    this.body = null;
    var headerView = new DataView(data, 0, BINARY_EXTENSION_HEADER_LENGTH);
    this.header = {
      magic: THREE.LoaderUtils.decodeText(new Uint8Array(data.slice(0, 4))),
      version: headerView.getUint32(4, true),
      length: headerView.getUint32(8, true)
    };

    if (this.header.magic !== BINARY_EXTENSION_HEADER_MAGIC) {
      throw new Error('THREE.GLTFLoader: Unsupported glTF-Binary header.');
    } else if (this.header.version < 2.0) {
      throw new Error('THREE.GLTFLoader: Legacy binary file detected.');
    }

    var chunkContentsLength = this.header.length - BINARY_EXTENSION_HEADER_LENGTH;
    var chunkView = new DataView(data, BINARY_EXTENSION_HEADER_LENGTH);
    var chunkIndex = 0;

    while (chunkIndex < chunkContentsLength) {
      var chunkLength = chunkView.getUint32(chunkIndex, true);
      chunkIndex += 4;
      var chunkType = chunkView.getUint32(chunkIndex, true);
      chunkIndex += 4;

      if (chunkType === BINARY_EXTENSION_CHUNK_TYPES.JSON) {
        var contentArray = new Uint8Array(data, BINARY_EXTENSION_HEADER_LENGTH + chunkIndex, chunkLength);
        this.content = THREE.LoaderUtils.decodeText(contentArray);
      } else if (chunkType === BINARY_EXTENSION_CHUNK_TYPES.BIN) {
        var byteOffset = BINARY_EXTENSION_HEADER_LENGTH + chunkIndex;
        this.body = data.slice(byteOffset, byteOffset + chunkLength);
      } // Clients must ignore chunks with unknown types.


      chunkIndex += chunkLength;
    }

    if (this.content === null) {
      throw new Error('THREE.GLTFLoader: JSON content not found.');
    }
  });
  /**
   * DRACO Mesh Compression Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Khronos/KHR_draco_mesh_compression
   */


  var GLTFDracoMeshCompressionExtension = /*#__PURE__*/function () {
    function GLTFDracoMeshCompressionExtension(json, dracoLoader) {
      _classCallCheck(this, GLTFDracoMeshCompressionExtension);

      if (!dracoLoader) {
        throw new Error('THREE.GLTFLoader: No DRACOLoader instance provided.');
      }

      this.name = EXTENSIONS.KHR_DRACO_MESH_COMPRESSION;
      this.json = json;
      this.dracoLoader = dracoLoader;
      this.dracoLoader.preload();
    }

    _createClass(GLTFDracoMeshCompressionExtension, [{
      key: "decodePrimitive",
      value: function decodePrimitive(primitive, parser) {
        var json = this.json;
        var dracoLoader = this.dracoLoader;
        var bufferViewIndex = primitive.extensions[this.name].bufferView;
        var gltfAttributeMap = primitive.extensions[this.name].attributes;
        var threeAttributeMap = {};
        var attributeNormalizedMap = {};
        var attributeTypeMap = {};

        for (var attributeName in gltfAttributeMap) {
          var threeAttributeName = ATTRIBUTES[attributeName] || attributeName.toLowerCase();
          threeAttributeMap[threeAttributeName] = gltfAttributeMap[attributeName];
        }

        for (var _attributeName in primitive.attributes) {
          var _threeAttributeName = ATTRIBUTES[_attributeName] || _attributeName.toLowerCase();

          if (gltfAttributeMap[_attributeName] !== undefined) {
            var accessorDef = json.accessors[primitive.attributes[_attributeName]];
            var componentType = WEBGL_COMPONENT_TYPES[accessorDef.componentType];
            attributeTypeMap[_threeAttributeName] = componentType;
            attributeNormalizedMap[_threeAttributeName] = accessorDef.normalized === true;
          }
        }

        return parser.getDependency('bufferView', bufferViewIndex).then(function (bufferView) {
          return new Promise(function (resolve) {
            dracoLoader.decodeDracoFile(bufferView, function (geometry) {
              for (var _attributeName2 in geometry.attributes) {
                var attribute = geometry.attributes[_attributeName2];
                var normalized = attributeNormalizedMap[_attributeName2];
                if (normalized !== undefined) attribute.normalized = normalized;
              }

              resolve(geometry);
            }, threeAttributeMap, attributeTypeMap);
          });
        });
      }
    }]);

    return GLTFDracoMeshCompressionExtension;
  }();
  /**
   * Texture Transform Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Khronos/KHR_texture_transform
   */


  var GLTFTextureTransformExtension = /*#__PURE__*/function () {
    function GLTFTextureTransformExtension() {
      _classCallCheck(this, GLTFTextureTransformExtension);

      this.name = EXTENSIONS.KHR_TEXTURE_TRANSFORM;
    }

    _createClass(GLTFTextureTransformExtension, [{
      key: "extendTexture",
      value: function extendTexture(texture, transform) {
        if (transform.texCoord !== undefined) {
          console.warn('THREE.GLTFLoader: Custom UV sets in "' + this.name + '" extension not yet supported.');
        }

        if (transform.offset === undefined && transform.rotation === undefined && transform.scale === undefined) {
          // See https://github.com/mrdoob/three.js/issues/21819.
          return texture;
        }

        texture = texture.clone();

        if (transform.offset !== undefined) {
          texture.offset.fromArray(transform.offset);
        }

        if (transform.rotation !== undefined) {
          texture.rotation = transform.rotation;
        }

        if (transform.scale !== undefined) {
          texture.repeat.fromArray(transform.scale);
        }

        texture.needsUpdate = true;
        return texture;
      }
    }]);

    return GLTFTextureTransformExtension;
  }();
  /**
   * Specular-Glossiness Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Archived/KHR_materials_pbrSpecularGlossiness
   */

  /**
   * A sub class of StandardMaterial with some of the functionality
   * changed via the `onBeforeCompile` callback
   * @pailhead
   */


  var GLTFMeshStandardSGMaterial = /*#__PURE__*/function (_MeshStandardMaterial) {
    _inherits(GLTFMeshStandardSGMaterial, _MeshStandardMaterial);

    var _super2 = _createSuper(GLTFMeshStandardSGMaterial);

    function GLTFMeshStandardSGMaterial(params) {
      var _this2;

      _classCallCheck(this, GLTFMeshStandardSGMaterial);

      _this2 = _super2.call(this);
      _this2.isGLTFSpecularGlossinessMaterial = true; //various chunks that need replacing

      var specularMapParsFragmentChunk = ['#ifdef USE_SPECULARMAP', '	uniform sampler2D specularMap;', '#endif'].join('\n');
      var glossinessMapParsFragmentChunk = ['#ifdef USE_GLOSSINESSMAP', '	uniform sampler2D glossinessMap;', '#endif'].join('\n');
      var specularMapFragmentChunk = ['vec3 specularFactor = specular;', '#ifdef USE_SPECULARMAP', '	vec4 texelSpecular = texture2D( specularMap, vUv );', '	// reads channel RGB, compatible with a glTF Specular-Glossiness (RGBA) texture', '	specularFactor *= texelSpecular.rgb;', '#endif'].join('\n');
      var glossinessMapFragmentChunk = ['float glossinessFactor = glossiness;', '#ifdef USE_GLOSSINESSMAP', '	vec4 texelGlossiness = texture2D( glossinessMap, vUv );', '	// reads channel A, compatible with a glTF Specular-Glossiness (RGBA) texture', '	glossinessFactor *= texelGlossiness.a;', '#endif'].join('\n');
      var lightPhysicalFragmentChunk = ['PhysicalMaterial material;', 'material.diffuseColor = diffuseColor.rgb * ( 1. - max( specularFactor.r, max( specularFactor.g, specularFactor.b ) ) );', 'vec3 dxy = max( abs( dFdx( geometryNormal ) ), abs( dFdy( geometryNormal ) ) );', 'float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );', 'material.roughness = max( 1.0 - glossinessFactor, 0.0525 ); // 0.0525 corresponds to the base mip of a 256 cubemap.', 'material.roughness += geometryRoughness;', 'material.roughness = min( material.roughness, 1.0 );', 'material.specularColor = specularFactor;'].join('\n');
      var uniforms = {
        specular: {
          value: new THREE.Color().setHex(0xffffff)
        },
        glossiness: {
          value: 1
        },
        specularMap: {
          value: null
        },
        glossinessMap: {
          value: null
        }
      };
      _this2._extraUniforms = uniforms;

      _this2.onBeforeCompile = function (shader) {
        for (var uniformName in uniforms) {
          shader.uniforms[uniformName] = uniforms[uniformName];
        }

        shader.fragmentShader = shader.fragmentShader.replace('uniform float roughness;', 'uniform vec3 specular;').replace('uniform float metalness;', 'uniform float glossiness;').replace('#include <roughnessmap_pars_fragment>', specularMapParsFragmentChunk).replace('#include <metalnessmap_pars_fragment>', glossinessMapParsFragmentChunk).replace('#include <roughnessmap_fragment>', specularMapFragmentChunk).replace('#include <metalnessmap_fragment>', glossinessMapFragmentChunk).replace('#include <lights_physical_fragment>', lightPhysicalFragmentChunk);
      };

      Object.defineProperties(_assertThisInitialized(_this2), {
        specular: {
          get: function get() {
            return uniforms.specular.value;
          },
          set: function set(v) {
            uniforms.specular.value = v;
          }
        },
        specularMap: {
          get: function get() {
            return uniforms.specularMap.value;
          },
          set: function set(v) {
            uniforms.specularMap.value = v;

            if (v) {
              this.defines.USE_SPECULARMAP = ''; // USE_UV is set by the renderer for specular maps
            } else {
              delete this.defines.USE_SPECULARMAP;
            }
          }
        },
        glossiness: {
          get: function get() {
            return uniforms.glossiness.value;
          },
          set: function set(v) {
            uniforms.glossiness.value = v;
          }
        },
        glossinessMap: {
          get: function get() {
            return uniforms.glossinessMap.value;
          },
          set: function set(v) {
            uniforms.glossinessMap.value = v;

            if (v) {
              this.defines.USE_GLOSSINESSMAP = '';
              this.defines.USE_UV = '';
            } else {
              delete this.defines.USE_GLOSSINESSMAP;
              delete this.defines.USE_UV;
            }
          }
        }
      });
      delete _this2.metalness;
      delete _this2.roughness;
      delete _this2.metalnessMap;
      delete _this2.roughnessMap;

      _this2.setValues(params);

      return _this2;
    }

    _createClass(GLTFMeshStandardSGMaterial, [{
      key: "copy",
      value: function copy(source) {
        _get(_getPrototypeOf(GLTFMeshStandardSGMaterial.prototype), "copy", this).call(this, source);

        this.specularMap = source.specularMap;
        this.specular.copy(source.specular);
        this.glossinessMap = source.glossinessMap;
        this.glossiness = source.glossiness;
        delete this.metalness;
        delete this.roughness;
        delete this.metalnessMap;
        delete this.roughnessMap;
        return this;
      }
    }]);

    return GLTFMeshStandardSGMaterial;
  }(THREE.MeshStandardMaterial);

  var GLTFMaterialsPbrSpecularGlossinessExtension = /*#__PURE__*/function () {
    function GLTFMaterialsPbrSpecularGlossinessExtension() {
      _classCallCheck(this, GLTFMaterialsPbrSpecularGlossinessExtension);

      this.name = EXTENSIONS.KHR_MATERIALS_PBR_SPECULAR_GLOSSINESS;
      this.specularGlossinessParams = ['color', 'map', 'lightMap', 'lightMapIntensity', 'aoMap', 'aoMapIntensity', 'emissive', 'emissiveIntensity', 'emissiveMap', 'bumpMap', 'bumpScale', 'normalMap', 'normalMapType', 'displacementMap', 'displacementScale', 'displacementBias', 'specularMap', 'specular', 'glossinessMap', 'glossiness', 'alphaMap', 'envMap', 'envMapIntensity'];
    }

    _createClass(GLTFMaterialsPbrSpecularGlossinessExtension, [{
      key: "getMaterialType",
      value: function getMaterialType() {
        return GLTFMeshStandardSGMaterial;
      }
    }, {
      key: "extendParams",
      value: function extendParams(materialParams, materialDef, parser) {
        var pbrSpecularGlossiness = materialDef.extensions[this.name];
        materialParams.color = new THREE.Color(1.0, 1.0, 1.0);
        materialParams.opacity = 1.0;
        var pending = [];

        if (Array.isArray(pbrSpecularGlossiness.diffuseFactor)) {
          var array = pbrSpecularGlossiness.diffuseFactor;
          materialParams.color.fromArray(array);
          materialParams.opacity = array[3];
        }

        if (pbrSpecularGlossiness.diffuseTexture !== undefined) {
          pending.push(parser.assignTexture(materialParams, 'map', pbrSpecularGlossiness.diffuseTexture, THREE.sRGBEncoding));
        }

        materialParams.emissive = new THREE.Color(0.0, 0.0, 0.0);
        materialParams.glossiness = pbrSpecularGlossiness.glossinessFactor !== undefined ? pbrSpecularGlossiness.glossinessFactor : 1.0;
        materialParams.specular = new THREE.Color(1.0, 1.0, 1.0);

        if (Array.isArray(pbrSpecularGlossiness.specularFactor)) {
          materialParams.specular.fromArray(pbrSpecularGlossiness.specularFactor);
        }

        if (pbrSpecularGlossiness.specularGlossinessTexture !== undefined) {
          var specGlossMapDef = pbrSpecularGlossiness.specularGlossinessTexture;
          pending.push(parser.assignTexture(materialParams, 'glossinessMap', specGlossMapDef));
          pending.push(parser.assignTexture(materialParams, 'specularMap', specGlossMapDef, THREE.sRGBEncoding));
        }

        return Promise.all(pending);
      }
    }, {
      key: "createMaterial",
      value: function createMaterial(materialParams) {
        var material = new GLTFMeshStandardSGMaterial(materialParams);
        material.fog = true;
        material.color = materialParams.color;
        material.map = materialParams.map === undefined ? null : materialParams.map;
        material.lightMap = null;
        material.lightMapIntensity = 1.0;
        material.aoMap = materialParams.aoMap === undefined ? null : materialParams.aoMap;
        material.aoMapIntensity = 1.0;
        material.emissive = materialParams.emissive;
        material.emissiveIntensity = materialParams.emissiveIntensity === undefined ? 1.0 : materialParams.emissiveIntensity;
        material.emissiveMap = materialParams.emissiveMap === undefined ? null : materialParams.emissiveMap;
        material.bumpMap = materialParams.bumpMap === undefined ? null : materialParams.bumpMap;
        material.bumpScale = 1;
        material.normalMap = materialParams.normalMap === undefined ? null : materialParams.normalMap;
        material.normalMapType = THREE.TangentSpaceNormalMap;
        if (materialParams.normalScale) material.normalScale = materialParams.normalScale;
        material.displacementMap = null;
        material.displacementScale = 1;
        material.displacementBias = 0;
        material.specularMap = materialParams.specularMap === undefined ? null : materialParams.specularMap;
        material.specular = materialParams.specular;
        material.glossinessMap = materialParams.glossinessMap === undefined ? null : materialParams.glossinessMap;
        material.glossiness = materialParams.glossiness;
        material.alphaMap = null;
        material.envMap = materialParams.envMap === undefined ? null : materialParams.envMap;
        material.envMapIntensity = 1.0;
        return material;
      }
    }]);

    return GLTFMaterialsPbrSpecularGlossinessExtension;
  }();
  /**
   * Mesh Quantization Extension
   *
   * Specification: https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Khronos/KHR_mesh_quantization
   */


  var GLTFMeshQuantizationExtension = /*#__PURE__*/_createClass(function GLTFMeshQuantizationExtension() {
    _classCallCheck(this, GLTFMeshQuantizationExtension);

    this.name = EXTENSIONS.KHR_MESH_QUANTIZATION;
  });
  /*********************************/

  /********** INTERPOLATION ********/

  /*********************************/
  // Spline Interpolation
  // Specification: https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#appendix-c-spline-interpolation


  var GLTFCubicSplineInterpolant = /*#__PURE__*/function (_Interpolant) {
    _inherits(GLTFCubicSplineInterpolant, _Interpolant);

    var _super3 = _createSuper(GLTFCubicSplineInterpolant);

    function GLTFCubicSplineInterpolant(parameterPositions, sampleValues, sampleSize, resultBuffer) {
      _classCallCheck(this, GLTFCubicSplineInterpolant);

      return _super3.call(this, parameterPositions, sampleValues, sampleSize, resultBuffer);
    }

    _createClass(GLTFCubicSplineInterpolant, [{
      key: "copySampleValue_",
      value: function copySampleValue_(index) {
        // Copies a sample value to the result buffer. See description of glTF
        // CUBICSPLINE values layout in interpolate_() function below.
        var result = this.resultBuffer,
            values = this.sampleValues,
            valueSize = this.valueSize,
            offset = index * valueSize * 3 + valueSize;

        for (var i = 0; i !== valueSize; i++) {
          result[i] = values[offset + i];
        }

        return result;
      }
    }]);

    return GLTFCubicSplineInterpolant;
  }(THREE.Interpolant);

  GLTFCubicSplineInterpolant.prototype.interpolate_ = function (i1, t0, t, t1) {
    var result = this.resultBuffer;
    var values = this.sampleValues;
    var stride = this.valueSize;
    var stride2 = stride * 2;
    var stride3 = stride * 3;
    var td = t1 - t0;
    var p = (t - t0) / td;
    var pp = p * p;
    var ppp = pp * p;
    var offset1 = i1 * stride3;
    var offset0 = offset1 - stride3;
    var s2 = -2 * ppp + 3 * pp;
    var s3 = ppp - pp;
    var s0 = 1 - s2;
    var s1 = s3 - pp + p; // Layout of keyframe output values for CUBICSPLINE animations:
    //   [ inTangent_1, splineVertex_1, outTangent_1, inTangent_2, splineVertex_2, ... ]

    for (var i = 0; i !== stride; i++) {
      var p0 = values[offset0 + i + stride]; // splineVertex_k

      var m0 = values[offset0 + i + stride2] * td; // outTangent_k * (t_k+1 - t_k)

      var p1 = values[offset1 + i + stride]; // splineVertex_k+1

      var m1 = values[offset1 + i] * td; // inTangent_k+1 * (t_k+1 - t_k)

      result[i] = s0 * p0 + s1 * m0 + s2 * p1 + s3 * m1;
    }

    return result;
  };

  var _q = new THREE.Quaternion();

  var GLTFCubicSplineQuaternionInterpolant = /*#__PURE__*/function (_GLTFCubicSplineInter) {
    _inherits(GLTFCubicSplineQuaternionInterpolant, _GLTFCubicSplineInter);

    var _super4 = _createSuper(GLTFCubicSplineQuaternionInterpolant);

    function GLTFCubicSplineQuaternionInterpolant() {
      _classCallCheck(this, GLTFCubicSplineQuaternionInterpolant);

      return _super4.apply(this, arguments);
    }

    _createClass(GLTFCubicSplineQuaternionInterpolant, [{
      key: "interpolate_",
      value: function interpolate_(i1, t0, t, t1) {
        var result = _get(_getPrototypeOf(GLTFCubicSplineQuaternionInterpolant.prototype), "interpolate_", this).call(this, i1, t0, t, t1);

        _q.fromArray(result).normalize().toArray(result);

        return result;
      }
    }]);

    return GLTFCubicSplineQuaternionInterpolant;
  }(GLTFCubicSplineInterpolant);
  /*********************************/

  /********** INTERNALS ************/

  /*********************************/

  /* CONSTANTS */


  var WEBGL_CONSTANTS = {
    FLOAT: 5126,
    //FLOAT_MAT2: 35674,
    FLOAT_MAT3: 35675,
    FLOAT_MAT4: 35676,
    FLOAT_VEC2: 35664,
    FLOAT_VEC3: 35665,
    FLOAT_VEC4: 35666,
    LINEAR: 9729,
    REPEAT: 10497,
    SAMPLER_2D: 35678,
    POINTS: 0,
    LINES: 1,
    LINE_LOOP: 2,
    LINE_STRIP: 3,
    TRIANGLES: 4,
    TRIANGLE_STRIP: 5,
    TRIANGLE_FAN: 6,
    UNSIGNED_BYTE: 5121,
    UNSIGNED_SHORT: 5123
  };
  var WEBGL_COMPONENT_TYPES = {
    5120: Int8Array,
    5121: Uint8Array,
    5122: Int16Array,
    5123: Uint16Array,
    5125: Uint32Array,
    5126: Float32Array
  };
  var WEBGL_FILTERS = {
    9728: THREE.NearestFilter,
    9729: THREE.LinearFilter,
    9984: THREE.NearestMipmapNearestFilter,
    9985: THREE.LinearMipmapNearestFilter,
    9986: THREE.NearestMipmapLinearFilter,
    9987: THREE.LinearMipmapLinearFilter
  };
  var WEBGL_WRAPPINGS = {
    33071: THREE.ClampToEdgeWrapping,
    33648: THREE.MirroredRepeatWrapping,
    10497: THREE.RepeatWrapping
  };
  var WEBGL_TYPE_SIZES = {
    'SCALAR': 1,
    'VEC2': 2,
    'VEC3': 3,
    'VEC4': 4,
    'MAT2': 4,
    'MAT3': 9,
    'MAT4': 16
  };
  var ATTRIBUTES = {
    POSITION: 'position',
    NORMAL: 'normal',
    TANGENT: 'tangent',
    TEXCOORD_0: 'uv',
    TEXCOORD_1: 'uv2',
    COLOR_0: 'color',
    WEIGHTS_0: 'skinWeight',
    JOINTS_0: 'skinIndex'
  };
  var PATH_PROPERTIES = {
    scale: 'scale',
    translation: 'position',
    rotation: 'quaternion',
    weights: 'morphTargetInfluences'
  };
  var INTERPOLATION = {
    CUBICSPLINE: undefined,
    // keyframe track will be initialized with a default interpolation type, then modified.
    LINEAR: THREE.InterpolateLinear,
    STEP: THREE.InterpolateDiscrete
  };
  var ALPHA_MODES = {
    OPAQUE: 'OPAQUE',
    MASK: 'MASK',
    BLEND: 'BLEND'
  };
  /**
   * Specification: https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#default-material
   */

  function createDefaultMaterial(cache) {
    if (cache['DefaultMaterial'] === undefined) {
      cache['DefaultMaterial'] = new THREE.MeshStandardMaterial({
        color: 0xFFFFFF,
        emissive: 0x000000,
        metalness: 1,
        roughness: 1,
        transparent: false,
        depthTest: true,
        side: THREE.FrontSide
      });
    }

    return cache['DefaultMaterial'];
  }

  function addUnknownExtensionsToUserData(knownExtensions, object, objectDef) {
    // Add unknown glTF extensions to an object's userData.
    for (var name in objectDef.extensions) {
      if (knownExtensions[name] === undefined) {
        object.userData.gltfExtensions = object.userData.gltfExtensions || {};
        object.userData.gltfExtensions[name] = objectDef.extensions[name];
      }
    }
  }
  /**
   * @param {Object3D|Material|BufferGeometry} object
   * @param {GLTF.definition} gltfDef
   */


  function assignExtrasToUserData(object, gltfDef) {
    if (gltfDef.extras !== undefined) {
      if (_typeof(gltfDef.extras) === 'object') {
        Object.assign(object.userData, gltfDef.extras);
      } else {
        console.warn('THREE.GLTFLoader: Ignoring primitive type .extras, ' + gltfDef.extras);
      }
    }
  }
  /**
   * Specification: https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#morph-targets
   *
   * @param {BufferGeometry} geometry
   * @param {Array<GLTF.Target>} targets
   * @param {GLTFParser} parser
   * @return {Promise<BufferGeometry>}
   */


  function addMorphTargets(geometry, targets, parser) {
    var hasMorphPosition = false;
    var hasMorphNormal = false;
    var hasMorphColor = false;

    for (var i = 0, il = targets.length; i < il; i++) {
      var target = targets[i];
      if (target.POSITION !== undefined) hasMorphPosition = true;
      if (target.NORMAL !== undefined) hasMorphNormal = true;
      if (target.COLOR_0 !== undefined) hasMorphColor = true;
      if (hasMorphPosition && hasMorphNormal && hasMorphColor) break;
    }

    if (!hasMorphPosition && !hasMorphNormal && !hasMorphColor) return Promise.resolve(geometry);
    var pendingPositionAccessors = [];
    var pendingNormalAccessors = [];
    var pendingColorAccessors = [];

    for (var _i2 = 0, _il = targets.length; _i2 < _il; _i2++) {
      var _target = targets[_i2];

      if (hasMorphPosition) {
        var pendingAccessor = _target.POSITION !== undefined ? parser.getDependency('accessor', _target.POSITION) : geometry.attributes.position;
        pendingPositionAccessors.push(pendingAccessor);
      }

      if (hasMorphNormal) {
        var _pendingAccessor = _target.NORMAL !== undefined ? parser.getDependency('accessor', _target.NORMAL) : geometry.attributes.normal;

        pendingNormalAccessors.push(_pendingAccessor);
      }

      if (hasMorphColor) {
        var _pendingAccessor2 = _target.COLOR_0 !== undefined ? parser.getDependency('accessor', _target.COLOR_0) : geometry.attributes.color;

        pendingColorAccessors.push(_pendingAccessor2);
      }
    }

    return Promise.all([Promise.all(pendingPositionAccessors), Promise.all(pendingNormalAccessors), Promise.all(pendingColorAccessors)]).then(function (accessors) {
      var morphPositions = accessors[0];
      var morphNormals = accessors[1];
      var morphColors = accessors[2];
      if (hasMorphPosition) geometry.morphAttributes.position = morphPositions;
      if (hasMorphNormal) geometry.morphAttributes.normal = morphNormals;
      if (hasMorphColor) geometry.morphAttributes.color = morphColors;
      geometry.morphTargetsRelative = true;
      return geometry;
    });
  }
  /**
   * @param {Mesh} mesh
   * @param {GLTF.Mesh} meshDef
   */


  function updateMorphTargets(mesh, meshDef) {
    mesh.updateMorphTargets();

    if (meshDef.weights !== undefined) {
      for (var i = 0, il = meshDef.weights.length; i < il; i++) {
        mesh.morphTargetInfluences[i] = meshDef.weights[i];
      }
    } // .extras has user-defined data, so check that .extras.targetNames is an array.


    if (meshDef.extras && Array.isArray(meshDef.extras.targetNames)) {
      var targetNames = meshDef.extras.targetNames;

      if (mesh.morphTargetInfluences.length === targetNames.length) {
        mesh.morphTargetDictionary = {};

        for (var _i3 = 0, _il2 = targetNames.length; _i3 < _il2; _i3++) {
          mesh.morphTargetDictionary[targetNames[_i3]] = _i3;
        }
      } else {
        console.warn('THREE.GLTFLoader: Invalid extras.targetNames length. Ignoring names.');
      }
    }
  }

  function createPrimitiveKey(primitiveDef) {
    var dracoExtension = primitiveDef.extensions && primitiveDef.extensions[EXTENSIONS.KHR_DRACO_MESH_COMPRESSION];
    var geometryKey;

    if (dracoExtension) {
      geometryKey = 'draco:' + dracoExtension.bufferView + ':' + dracoExtension.indices + ':' + createAttributesKey(dracoExtension.attributes);
    } else {
      geometryKey = primitiveDef.indices + ':' + createAttributesKey(primitiveDef.attributes) + ':' + primitiveDef.mode;
    }

    return geometryKey;
  }

  function createAttributesKey(attributes) {
    var attributesKey = '';
    var keys = Object.keys(attributes).sort();

    for (var i = 0, il = keys.length; i < il; i++) {
      attributesKey += keys[i] + ':' + attributes[keys[i]] + ';';
    }

    return attributesKey;
  }

  function getNormalizedComponentScale(constructor) {
    // Reference:
    // https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Khronos/KHR_mesh_quantization#encoding-quantized-data
    switch (constructor) {
      case Int8Array:
        return 1 / 127;

      case Uint8Array:
        return 1 / 255;

      case Int16Array:
        return 1 / 32767;

      case Uint16Array:
        return 1 / 65535;

      default:
        throw new Error('THREE.GLTFLoader: Unsupported normalized accessor component type.');
    }
  }

  function getImageURIMimeType(uri) {
    if (uri.search(/\.jpe?g($|\?)/i) > 0 || uri.search(/^data\:image\/jpeg/) === 0) return 'image/jpeg';
    if (uri.search(/\.webp($|\?)/i) > 0 || uri.search(/^data\:image\/webp/) === 0) return 'image/webp';
    return 'image/png';
  }
  /* GLTF PARSER */


  var GLTFParser = /*#__PURE__*/function () {
    function GLTFParser() {
      var json = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
      var options = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};

      _classCallCheck(this, GLTFParser);

      this.json = json;
      this.extensions = {};
      this.plugins = {};
      this.options = options; // loader object cache

      this.cache = new GLTFRegistry(); // associations between Three.js objects and glTF elements

      this.associations = new Map(); // BufferGeometry caching

      this.primitiveCache = {}; // Object3D instance caches

      this.meshCache = {
        refs: {},
        uses: {}
      };
      this.cameraCache = {
        refs: {},
        uses: {}
      };
      this.lightCache = {
        refs: {},
        uses: {}
      };
      this.sourceCache = {};
      this.textureCache = {}; // Track node names, to ensure no duplicates

      this.nodeNamesUsed = {}; // Use an ImageBitmapLoader if imageBitmaps are supported. Moves much of the
      // expensive work of uploading a texture to the GPU off the main thread.

      var isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent) === true;
      var isFirefox = navigator.userAgent.indexOf('Firefox') > -1;
      var firefoxVersion = isFirefox ? navigator.userAgent.match(/Firefox\/([0-9]+)\./)[1] : -1;

      if (typeof createImageBitmap === 'undefined' || isSafari || isFirefox && firefoxVersion < 98) {
        this.textureLoader = new THREE.TextureLoader(this.options.manager);
      } else {
        this.textureLoader = new THREE.ImageBitmapLoader(this.options.manager);
      }

      this.textureLoader.setCrossOrigin(this.options.crossOrigin);
      this.textureLoader.setRequestHeader(this.options.requestHeader);
      this.fileLoader = new THREE.FileLoader(this.options.manager);
      this.fileLoader.setResponseType('arraybuffer');

      if (this.options.crossOrigin === 'use-credentials') {
        this.fileLoader.setWithCredentials(true);
      }
    }

    _createClass(GLTFParser, [{
      key: "setExtensions",
      value: function setExtensions(extensions) {
        this.extensions = extensions;
      }
    }, {
      key: "setPlugins",
      value: function setPlugins(plugins) {
        this.plugins = plugins;
      }
    }, {
      key: "parse",
      value: function parse(onLoad, onError) {
        var parser = this;
        var json = this.json;
        var extensions = this.extensions; // Clear the loader cache

        this.cache.removeAll(); // Mark the special nodes/meshes in json for efficient parse

        this._invokeAll(function (ext) {
          return ext._markDefs && ext._markDefs();
        });

        Promise.all(this._invokeAll(function (ext) {
          return ext.beforeRoot && ext.beforeRoot();
        })).then(function () {
          return Promise.all([parser.getDependencies('scene'), parser.getDependencies('animation'), parser.getDependencies('camera')]);
        }).then(function (dependencies) {
          var result = {
            scene: dependencies[0][json.scene || 0],
            scenes: dependencies[0],
            animations: dependencies[1],
            cameras: dependencies[2],
            asset: json.asset,
            parser: parser,
            userData: {}
          };
          addUnknownExtensionsToUserData(extensions, result, json);
          assignExtrasToUserData(result, json);
          Promise.all(parser._invokeAll(function (ext) {
            return ext.afterRoot && ext.afterRoot(result);
          })).then(function () {
            onLoad(result);
          });
        })["catch"](onError);
      }
      /**
       * Marks the special nodes/meshes in json for efficient parse.
       */

    }, {
      key: "_markDefs",
      value: function _markDefs() {
        var nodeDefs = this.json.nodes || [];
        var skinDefs = this.json.skins || [];
        var meshDefs = this.json.meshes || []; // Nothing in the node definition indicates whether it is a Bone or an
        // Object3D. Use the skins' joint references to mark bones.

        for (var skinIndex = 0, skinLength = skinDefs.length; skinIndex < skinLength; skinIndex++) {
          var joints = skinDefs[skinIndex].joints;

          for (var i = 0, il = joints.length; i < il; i++) {
            nodeDefs[joints[i]].isBone = true;
          }
        } // Iterate over all nodes, marking references to shared resources,
        // as well as skeleton joints.


        for (var nodeIndex = 0, nodeLength = nodeDefs.length; nodeIndex < nodeLength; nodeIndex++) {
          var nodeDef = nodeDefs[nodeIndex];

          if (nodeDef.mesh !== undefined) {
            this._addNodeRef(this.meshCache, nodeDef.mesh); // Nothing in the mesh definition indicates whether it is
            // a SkinnedMesh or Mesh. Use the node's mesh reference
            // to mark SkinnedMesh if node has skin.


            if (nodeDef.skin !== undefined) {
              meshDefs[nodeDef.mesh].isSkinnedMesh = true;
            }
          }

          if (nodeDef.camera !== undefined) {
            this._addNodeRef(this.cameraCache, nodeDef.camera);
          }
        }
      }
      /**
       * Counts references to shared node / Object3D resources. These resources
       * can be reused, or "instantiated", at multiple nodes in the scene
       * hierarchy. Mesh, Camera, and Light instances are instantiated and must
       * be marked. Non-scenegraph resources (like Materials, Geometries, and
       * Textures) can be reused directly and are not marked here.
       *
       * Example: CesiumMilkTruck sample model reuses "Wheel" meshes.
       */

    }, {
      key: "_addNodeRef",
      value: function _addNodeRef(cache, index) {
        if (index === undefined) return;

        if (cache.refs[index] === undefined) {
          cache.refs[index] = cache.uses[index] = 0;
        }

        cache.refs[index]++;
      }
      /** Returns a reference to a shared resource, cloning it if necessary. */

    }, {
      key: "_getNodeRef",
      value: function _getNodeRef(cache, index, object) {
        var _this3 = this;

        if (cache.refs[index] <= 1) return object;
        var ref = object.clone(); // Propagates mappings to the cloned object, prevents mappings on the
        // original object from being lost.

        var updateMappings = function updateMappings(original, clone) {
          var mappings = _this3.associations.get(original);

          if (mappings != null) {
            _this3.associations.set(clone, mappings);
          }

          var _iterator = _createForOfIteratorHelper(original.children.entries()),
              _step;

          try {
            for (_iterator.s(); !(_step = _iterator.n()).done;) {
              var _step$value = _slicedToArray(_step.value, 2),
                  i = _step$value[0],
                  child = _step$value[1];

              updateMappings(child, clone.children[i]);
            }
          } catch (err) {
            _iterator.e(err);
          } finally {
            _iterator.f();
          }
        };

        updateMappings(object, ref);
        ref.name += '_instance_' + cache.uses[index]++;
        return ref;
      }
    }, {
      key: "_invokeOne",
      value: function _invokeOne(func) {
        var extensions = Object.values(this.plugins);
        extensions.push(this);

        for (var i = 0; i < extensions.length; i++) {
          var result = func(extensions[i]);
          if (result) return result;
        }

        return null;
      }
    }, {
      key: "_invokeAll",
      value: function _invokeAll(func) {
        var extensions = Object.values(this.plugins);
        extensions.unshift(this);
        var pending = [];

        for (var i = 0; i < extensions.length; i++) {
          var result = func(extensions[i]);
          if (result) pending.push(result);
        }

        return pending;
      }
      /**
       * Requests the specified dependency asynchronously, with caching.
       * @param {string} type
       * @param {number} index
       * @return {Promise<Object3D|Material|THREE.Texture|AnimationClip|ArrayBuffer|Object>}
       */

    }, {
      key: "getDependency",
      value: function getDependency(type, index) {
        var cacheKey = type + ':' + index;
        var dependency = this.cache.get(cacheKey);

        if (!dependency) {
          switch (type) {
            case 'scene':
              dependency = this.loadScene(index);
              break;

            case 'node':
              dependency = this.loadNode(index);
              break;

            case 'mesh':
              dependency = this._invokeOne(function (ext) {
                return ext.loadMesh && ext.loadMesh(index);
              });
              break;

            case 'accessor':
              dependency = this.loadAccessor(index);
              break;

            case 'bufferView':
              dependency = this._invokeOne(function (ext) {
                return ext.loadBufferView && ext.loadBufferView(index);
              });
              break;

            case 'buffer':
              dependency = this.loadBuffer(index);
              break;

            case 'material':
              dependency = this._invokeOne(function (ext) {
                return ext.loadMaterial && ext.loadMaterial(index);
              });
              break;

            case 'texture':
              dependency = this._invokeOne(function (ext) {
                return ext.loadTexture && ext.loadTexture(index);
              });
              break;

            case 'skin':
              dependency = this.loadSkin(index);
              break;

            case 'animation':
              dependency = this._invokeOne(function (ext) {
                return ext.loadAnimation && ext.loadAnimation(index);
              });
              break;

            case 'camera':
              dependency = this.loadCamera(index);
              break;

            default:
              throw new Error('Unknown type: ' + type);
          }

          this.cache.add(cacheKey, dependency);
        }

        return dependency;
      }
      /**
       * Requests all dependencies of the specified type asynchronously, with caching.
       * @param {string} type
       * @return {Promise<Array<Object>>}
       */

    }, {
      key: "getDependencies",
      value: function getDependencies(type) {
        var dependencies = this.cache.get(type);

        if (!dependencies) {
          var parser = this;
          var defs = this.json[type + (type === 'mesh' ? 'es' : 's')] || [];
          dependencies = Promise.all(defs.map(function (def, index) {
            return parser.getDependency(type, index);
          }));
          this.cache.add(type, dependencies);
        }

        return dependencies;
      }
      /**
       * Specification: https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#buffers-and-buffer-views
       * @param {number} bufferIndex
       * @return {Promise<ArrayBuffer>}
       */

    }, {
      key: "loadBuffer",
      value: function loadBuffer(bufferIndex) {
        var bufferDef = this.json.buffers[bufferIndex];
        var loader = this.fileLoader;

        if (bufferDef.type && bufferDef.type !== 'arraybuffer') {
          throw new Error('THREE.GLTFLoader: ' + bufferDef.type + ' buffer type is not supported.');
        } // If present, GLB container is required to be the first buffer.


        if (bufferDef.uri === undefined && bufferIndex === 0) {
          return Promise.resolve(this.extensions[EXTENSIONS.KHR_BINARY_GLTF].body);
        }

        var options = this.options;
        return new Promise(function (resolve, reject) {
          loader.load(THREE.LoaderUtils.resolveURL(bufferDef.uri, options.path), resolve, undefined, function () {
            reject(new Error('THREE.GLTFLoader: Failed to load buffer "' + bufferDef.uri + '".'));
          });
        });
      }
      /**
       * Specification: https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#buffers-and-buffer-views
       * @param {number} bufferViewIndex
       * @return {Promise<ArrayBuffer>}
       */

    }, {
      key: "loadBufferView",
      value: function loadBufferView(bufferViewIndex) {
        var bufferViewDef = this.json.bufferViews[bufferViewIndex];
        return this.getDependency('buffer', bufferViewDef.buffer).then(function (buffer) {
          var byteLength = bufferViewDef.byteLength || 0;
          var byteOffset = bufferViewDef.byteOffset || 0;
          return buffer.slice(byteOffset, byteOffset + byteLength);
        });
      }
      /**
       * Specification: https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#accessors
       * @param {number} accessorIndex
       * @return {Promise<BufferAttribute|InterleavedBufferAttribute>}
       */

    }, {
      key: "loadAccessor",
      value: function loadAccessor(accessorIndex) {
        var parser = this;
        var json = this.json;
        var accessorDef = this.json.accessors[accessorIndex];

        if (accessorDef.bufferView === undefined && accessorDef.sparse === undefined) {
          // Ignore empty accessors, which may be used to declare runtime
          // information about attributes coming from another source (e.g. Draco
          // compression extension).
          return Promise.resolve(null);
        }

        var pendingBufferViews = [];

        if (accessorDef.bufferView !== undefined) {
          pendingBufferViews.push(this.getDependency('bufferView', accessorDef.bufferView));
        } else {
          pendingBufferViews.push(null);
        }

        if (accessorDef.sparse !== undefined) {
          pendingBufferViews.push(this.getDependency('bufferView', accessorDef.sparse.indices.bufferView));
          pendingBufferViews.push(this.getDependency('bufferView', accessorDef.sparse.values.bufferView));
        }

        return Promise.all(pendingBufferViews).then(function (bufferViews) {
          var bufferView = bufferViews[0];
          var itemSize = WEBGL_TYPE_SIZES[accessorDef.type];
          var TypedArray = WEBGL_COMPONENT_TYPES[accessorDef.componentType]; // For VEC3: itemSize is 3, elementBytes is 4, itemBytes is 12.

          var elementBytes = TypedArray.BYTES_PER_ELEMENT;
          var itemBytes = elementBytes * itemSize;
          var byteOffset = accessorDef.byteOffset || 0;
          var byteStride = accessorDef.bufferView !== undefined ? json.bufferViews[accessorDef.bufferView].byteStride : undefined;
          var normalized = accessorDef.normalized === true;
          var array, bufferAttribute; // The buffer is not interleaved if the stride is the item size in bytes.

          if (byteStride && byteStride !== itemBytes) {
            // Each "slice" of the buffer, as defined by 'count' elements of 'byteStride' bytes, gets its own InterleavedBuffer
            // This makes sure that IBA.count reflects accessor.count properly
            var ibSlice = Math.floor(byteOffset / byteStride);
            var ibCacheKey = 'InterleavedBuffer:' + accessorDef.bufferView + ':' + accessorDef.componentType + ':' + ibSlice + ':' + accessorDef.count;
            var ib = parser.cache.get(ibCacheKey);

            if (!ib) {
              array = new TypedArray(bufferView, ibSlice * byteStride, accessorDef.count * byteStride / elementBytes); // Integer parameters to IB/IBA are in array elements, not bytes.

              ib = new THREE.InterleavedBuffer(array, byteStride / elementBytes);
              parser.cache.add(ibCacheKey, ib);
            }

            bufferAttribute = new THREE.InterleavedBufferAttribute(ib, itemSize, byteOffset % byteStride / elementBytes, normalized);
          } else {
            if (bufferView === null) {
              array = new TypedArray(accessorDef.count * itemSize);
            } else {
              array = new TypedArray(bufferView, byteOffset, accessorDef.count * itemSize);
            }

            bufferAttribute = new THREE.BufferAttribute(array, itemSize, normalized);
          } // https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#sparse-accessors


          if (accessorDef.sparse !== undefined) {
            var itemSizeIndices = WEBGL_TYPE_SIZES.SCALAR;
            var TypedArrayIndices = WEBGL_COMPONENT_TYPES[accessorDef.sparse.indices.componentType];
            var byteOffsetIndices = accessorDef.sparse.indices.byteOffset || 0;
            var byteOffsetValues = accessorDef.sparse.values.byteOffset || 0;
            var sparseIndices = new TypedArrayIndices(bufferViews[1], byteOffsetIndices, accessorDef.sparse.count * itemSizeIndices);
            var sparseValues = new TypedArray(bufferViews[2], byteOffsetValues, accessorDef.sparse.count * itemSize);

            if (bufferView !== null) {
              // Avoid modifying the original ArrayBuffer, if the bufferView wasn't initialized with zeroes.
              bufferAttribute = new THREE.BufferAttribute(bufferAttribute.array.slice(), bufferAttribute.itemSize, bufferAttribute.normalized);
            }

            for (var i = 0, il = sparseIndices.length; i < il; i++) {
              var index = sparseIndices[i];
              bufferAttribute.setX(index, sparseValues[i * itemSize]);
              if (itemSize >= 2) bufferAttribute.setY(index, sparseValues[i * itemSize + 1]);
              if (itemSize >= 3) bufferAttribute.setZ(index, sparseValues[i * itemSize + 2]);
              if (itemSize >= 4) bufferAttribute.setW(index, sparseValues[i * itemSize + 3]);
              if (itemSize >= 5) throw new Error('THREE.GLTFLoader: Unsupported itemSize in sparse BufferAttribute.');
            }
          }

          return bufferAttribute;
        });
      }
      /**
       * Specification: https://github.com/KhronosGroup/glTF/tree/master/specification/2.0#textures
       * @param {number} textureIndex
       * @return {Promise<THREE.Texture>}
       */

    }, {
      key: "loadTexture",
      value: function loadTexture(textureIndex) {
        var json = this.json;
        var options = this.options;
        var textureDef = json.textures[textureIndex];
        var sourceIndex = textureDef.source;
        var sourceDef = json.images[sourceIndex];
        var loader = this.textureLoader;

        if (sourceDef.uri) {
          var handler = options.manager.getHandler(sourceDef.uri);
          if (handler !== null) loader = handler;
        }

        return this.loadTextureImage(textureIndex, sourceIndex, loader);
      }
    }, {
      key: "loadTextureImage",
      value: function loadTextureImage(textureIndex, sourceIndex, loader) {
        var parser = this;
        var json = this.json;
        var textureDef = json.textures[textureIndex];
        var sourceDef = json.images[sourceIndex];
        var cacheKey = (sourceDef.uri || sourceDef.bufferView) + ':' + textureDef.sampler;

        if (this.textureCache[cacheKey]) {
          // See https://github.com/mrdoob/three.js/issues/21559.
          return this.textureCache[cacheKey];
        }

        var promise = this.loadImageSource(sourceIndex, loader).then(function (texture) {
          texture.flipY = false;
          if (textureDef.name) texture.name = textureDef.name;
          var samplers = json.samplers || {};
          var sampler = samplers[textureDef.sampler] || {};
          texture.magFilter = WEBGL_FILTERS[sampler.magFilter] || THREE.LinearFilter;
          texture.minFilter = WEBGL_FILTERS[sampler.minFilter] || THREE.LinearMipmapLinearFilter;
          texture.wrapS = WEBGL_WRAPPINGS[sampler.wrapS] || THREE.RepeatWrapping;
          texture.wrapT = WEBGL_WRAPPINGS[sampler.wrapT] || THREE.RepeatWrapping;
          parser.associations.set(texture, {
            textures: textureIndex
          });
          return texture;
        })["catch"](function () {
          return null;
        });
        this.textureCache[cacheKey] = promise;
        return promise;
      }
    }, {
      key: "loadImageSource",
      value: function loadImageSource(sourceIndex, loader) {
        var parser = this;
        var json = this.json;
        var options = this.options;

        if (this.sourceCache[sourceIndex] !== undefined) {
          return this.sourceCache[sourceIndex].then(function (texture) {
            return texture.clone();
          });
        }

        var sourceDef = json.images[sourceIndex];
        var URL = self.URL || self.webkitURL;
        var sourceURI = sourceDef.uri || '';
        var isObjectURL = false;

        if (sourceDef.bufferView !== undefined) {
          // Load binary image data from bufferView, if provided.
          sourceURI = parser.getDependency('bufferView', sourceDef.bufferView).then(function (bufferView) {
            isObjectURL = true;
            var blob = new Blob([bufferView], {
              type: sourceDef.mimeType
            });
            sourceURI = URL.createObjectURL(blob);
            return sourceURI;
          });
        } else if (sourceDef.uri === undefined) {
          throw new Error('THREE.GLTFLoader: Image ' + sourceIndex + ' is missing URI and bufferView');
        }

        var promise = Promise.resolve(sourceURI).then(function (sourceURI) {
          return new Promise(function (resolve, reject) {
            var onLoad = resolve;

            if (loader.isImageBitmapLoader === true) {
              onLoad = function onLoad(imageBitmap) {
                var texture = new THREE.Texture(imageBitmap);
                texture.needsUpdate = true;
                resolve(texture);
              };
            }

            loader.load(THREE.LoaderUtils.resolveURL(sourceURI, options.path), onLoad, undefined, reject);
          });
        }).then(function (texture) {
          // Clean up resources and configure Texture.
          if (isObjectURL === true) {
            URL.revokeObjectURL(sourceURI);
          }

          texture.userData.mimeType = sourceDef.mimeType || getImageURIMimeType(sourceDef.uri);
          return texture;
        })["catch"](function (error) {
          console.error('THREE.GLTFLoader: Couldn\'t load texture', sourceURI);
          throw error;
        });
        this.sourceCache[sourceIndex] = promise;
        return promise;
      }
      /**
       * Asynchronously assigns a texture to the given material parameters.
       * @param {Object} materialParams
       * @param {string} mapName
       * @param {Object} mapDef
       * @return {Promise<Texture>}
       */

    }, {
      key: "assignTexture",
      value: function assignTexture(materialParams, mapName, mapDef, encoding) {
        var parser = this;
        return this.getDependency('texture', mapDef.index).then(function (texture) {
          // Materials sample aoMap from UV set 1 and other maps from UV set 0 - this can't be configured
          // However, we will copy UV set 0 to UV set 1 on demand for aoMap
          if (mapDef.texCoord !== undefined && mapDef.texCoord != 0 && !(mapName === 'aoMap' && mapDef.texCoord == 1)) {
            console.warn('THREE.GLTFLoader: Custom UV set ' + mapDef.texCoord + ' for texture ' + mapName + ' not yet supported.');
          }

          if (parser.extensions[EXTENSIONS.KHR_TEXTURE_TRANSFORM]) {
            var transform = mapDef.extensions !== undefined ? mapDef.extensions[EXTENSIONS.KHR_TEXTURE_TRANSFORM] : undefined;

            if (transform) {
              var gltfReference = parser.associations.get(texture);
              texture = parser.extensions[EXTENSIONS.KHR_TEXTURE_TRANSFORM].extendTexture(texture, transform);
              parser.associations.set(texture, gltfReference);
            }
          }

          if (encoding !== undefined) {
            texture.encoding = encoding;
          }

          materialParams[mapName] = texture;
          return texture;
        });
      }
      /**
       * Assigns final material to a Mesh, Line, or Points instance. The instance
       * already has a material (generated from the glTF material options alone)
       * but reuse of the same glTF material may require multiple threejs materials
       * to accommodate different primitive types, defines, etc. New materials will
       * be created if necessary, and reused from a cache.
       * @param  {Object3D} mesh Mesh, Line, or Points instance.
       */

    }, {
      key: "assignFinalMaterial",
      value: function assignFinalMaterial(mesh) {
        var geometry = mesh.geometry;
        var material = mesh.material;
        var useDerivativeTangents = geometry.attributes.tangent === undefined;
        var useVertexColors = geometry.attributes.color !== undefined;
        var useFlatShading = geometry.attributes.normal === undefined;

        if (mesh.isPoints) {
          var cacheKey = 'PointsMaterial:' + material.uuid;
          var pointsMaterial = this.cache.get(cacheKey);

          if (!pointsMaterial) {
            pointsMaterial = new THREE.PointsMaterial();
            THREE.Material.prototype.copy.call(pointsMaterial, material);
            pointsMaterial.color.copy(material.color);
            pointsMaterial.map = material.map;
            pointsMaterial.sizeAttenuation = false; // glTF spec says points should be 1px

            this.cache.add(cacheKey, pointsMaterial);
          }

          material = pointsMaterial;
        } else if (mesh.isLine) {
          var _cacheKey = 'LineBasicMaterial:' + material.uuid;

          var lineMaterial = this.cache.get(_cacheKey);

          if (!lineMaterial) {
            lineMaterial = new THREE.LineBasicMaterial();
            THREE.Material.prototype.copy.call(lineMaterial, material);
            lineMaterial.color.copy(material.color);
            this.cache.add(_cacheKey, lineMaterial);
          }

          material = lineMaterial;
        } // Clone the material if it will be modified


        if (useDerivativeTangents || useVertexColors || useFlatShading) {
          var _cacheKey2 = 'ClonedMaterial:' + material.uuid + ':';

          if (material.isGLTFSpecularGlossinessMaterial) _cacheKey2 += 'specular-glossiness:';
          if (useDerivativeTangents) _cacheKey2 += 'derivative-tangents:';
          if (useVertexColors) _cacheKey2 += 'vertex-colors:';
          if (useFlatShading) _cacheKey2 += 'flat-shading:';
          var cachedMaterial = this.cache.get(_cacheKey2);

          if (!cachedMaterial) {
            cachedMaterial = material.clone();
            if (useVertexColors) cachedMaterial.vertexColors = true;
            if (useFlatShading) cachedMaterial.flatShading = true;

            if (useDerivativeTangents) {
              // https://github.com/mrdoob/three.js/issues/11438#issuecomment-507003995
              if (cachedMaterial.normalScale) cachedMaterial.normalScale.y *= -1;
              if (cachedMaterial.clearcoatNormalScale) cachedMaterial.clearcoatNormalScale.y *= -1;
            }

            this.cache.add(_cacheKey2, cachedMaterial);
            this.associations.set(cachedMaterial, this.associations.get(material));
          }

          material = cachedMaterial;
        } // workarounds for mesh and geometry


        if (material.aoMap && geometry.attributes.uv2 === undefined && geometry.attributes.uv !== undefined) {
          geometry.setAttribute('uv2', geometry.attributes.uv);
        }

        mesh.material = material;
      }
    }, {
      key: "getMaterialType",
      value: function
        /* materialIndex */
      getMaterialType() {
        return THREE.MeshStandardMaterial;
      }
      /**
       * Specification: https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#materials
       * @param {number} materialIndex
       * @return {Promise<Material>}
       */

    }, {
      key: "loadMaterial",
      value: function loadMaterial(materialIndex) {
        var parser = this;
        var json = this.json;
        var extensions = this.extensions;
        var materialDef = json.materials[materialIndex];
        var materialType;
        var materialParams = {};
        var materialExtensions = materialDef.extensions || {};
        var pending = [];

        if (materialExtensions[EXTENSIONS.KHR_MATERIALS_PBR_SPECULAR_GLOSSINESS]) {
          var sgExtension = extensions[EXTENSIONS.KHR_MATERIALS_PBR_SPECULAR_GLOSSINESS];
          materialType = sgExtension.getMaterialType();
          pending.push(sgExtension.extendParams(materialParams, materialDef, parser));
        } else if (materialExtensions[EXTENSIONS.KHR_MATERIALS_UNLIT]) {
          var kmuExtension = extensions[EXTENSIONS.KHR_MATERIALS_UNLIT];
          materialType = kmuExtension.getMaterialType();
          pending.push(kmuExtension.extendParams(materialParams, materialDef, parser));
        } else {
          // Specification:
          // https://github.com/KhronosGroup/glTF/tree/master/specification/2.0#metallic-roughness-material
          var metallicRoughness = materialDef.pbrMetallicRoughness || {};
          materialParams.color = new THREE.Color(1.0, 1.0, 1.0);
          materialParams.opacity = 1.0;

          if (Array.isArray(metallicRoughness.baseColorFactor)) {
            var array = metallicRoughness.baseColorFactor;
            materialParams.color.fromArray(array);
            materialParams.opacity = array[3];
          }

          if (metallicRoughness.baseColorTexture !== undefined) {
            pending.push(parser.assignTexture(materialParams, 'map', metallicRoughness.baseColorTexture, THREE.sRGBEncoding));
          }

          materialParams.metalness = metallicRoughness.metallicFactor !== undefined ? metallicRoughness.metallicFactor : 1.0;
          materialParams.roughness = metallicRoughness.roughnessFactor !== undefined ? metallicRoughness.roughnessFactor : 1.0;

          if (metallicRoughness.metallicRoughnessTexture !== undefined) {
            pending.push(parser.assignTexture(materialParams, 'metalnessMap', metallicRoughness.metallicRoughnessTexture));
            pending.push(parser.assignTexture(materialParams, 'roughnessMap', metallicRoughness.metallicRoughnessTexture));
          }

          materialType = this._invokeOne(function (ext) {
            return ext.getMaterialType && ext.getMaterialType(materialIndex);
          });
          pending.push(Promise.all(this._invokeAll(function (ext) {
            return ext.extendMaterialParams && ext.extendMaterialParams(materialIndex, materialParams);
          })));
        }

        if (materialDef.doubleSided === true) {
          materialParams.side = THREE.DoubleSide;
        }

        var alphaMode = materialDef.alphaMode || ALPHA_MODES.OPAQUE;

        if (alphaMode === ALPHA_MODES.BLEND) {
          materialParams.transparent = true; // See: https://github.com/mrdoob/three.js/issues/17706

          materialParams.depthWrite = false;
        } else {
          materialParams.transparent = false;

          if (alphaMode === ALPHA_MODES.MASK) {
            materialParams.alphaTest = materialDef.alphaCutoff !== undefined ? materialDef.alphaCutoff : 0.5;
          }
        }

        if (materialDef.normalTexture !== undefined && materialType !== THREE.MeshBasicMaterial) {
          pending.push(parser.assignTexture(materialParams, 'normalMap', materialDef.normalTexture));
          materialParams.normalScale = new THREE.Vector2(1, 1);

          if (materialDef.normalTexture.scale !== undefined) {
            var scale = materialDef.normalTexture.scale;
            materialParams.normalScale.set(scale, scale);
          }
        }

        if (materialDef.occlusionTexture !== undefined && materialType !== THREE.MeshBasicMaterial) {
          pending.push(parser.assignTexture(materialParams, 'aoMap', materialDef.occlusionTexture));

          if (materialDef.occlusionTexture.strength !== undefined) {
            materialParams.aoMapIntensity = materialDef.occlusionTexture.strength;
          }
        }

        if (materialDef.emissiveFactor !== undefined && materialType !== THREE.MeshBasicMaterial) {
          materialParams.emissive = new THREE.Color().fromArray(materialDef.emissiveFactor);
        }

        if (materialDef.emissiveTexture !== undefined && materialType !== THREE.MeshBasicMaterial) {
          pending.push(parser.assignTexture(materialParams, 'emissiveMap', materialDef.emissiveTexture, THREE.sRGBEncoding));
        }

        return Promise.all(pending).then(function () {
          var material;

          if (materialType === GLTFMeshStandardSGMaterial) {
            material = extensions[EXTENSIONS.KHR_MATERIALS_PBR_SPECULAR_GLOSSINESS].createMaterial(materialParams);
          } else {
            material = new materialType(materialParams);
          }

          if (materialDef.name) material.name = materialDef.name;
          assignExtrasToUserData(material, materialDef);
          parser.associations.set(material, {
            materials: materialIndex
          });
          if (materialDef.extensions) addUnknownExtensionsToUserData(extensions, material, materialDef);
          return material;
        });
      }
      /** When Object3D instances are targeted by animation, they need unique names. */

    }, {
      key: "createUniqueName",
      value: function createUniqueName(originalName) {
        var sanitizedName = THREE.PropertyBinding.sanitizeNodeName(originalName || '');
        var name = sanitizedName;

        for (var i = 1; this.nodeNamesUsed[name]; ++i) {
          name = sanitizedName + '_' + i;
        }

        this.nodeNamesUsed[name] = true;
        return name;
      }
      /**
       * Specification: https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#geometry
       *
       * Creates BufferGeometries from primitives.
       *
       * @param {Array<GLTF.Primitive>} primitives
       * @return {Promise<Array<BufferGeometry>>}
       */

    }, {
      key: "loadGeometries",
      value: function loadGeometries(primitives) {
        var parser = this;
        var extensions = this.extensions;
        var cache = this.primitiveCache;

        function createDracoPrimitive(primitive) {
          return extensions[EXTENSIONS.KHR_DRACO_MESH_COMPRESSION].decodePrimitive(primitive, parser).then(function (geometry) {
            return addPrimitiveAttributes(geometry, primitive, parser);
          });
        }

        var pending = [];

        for (var i = 0, il = primitives.length; i < il; i++) {
          var primitive = primitives[i];
          var cacheKey = createPrimitiveKey(primitive); // See if we've already created this geometry

          var cached = cache[cacheKey];

          if (cached) {
            // Use the cached geometry if it exists
            pending.push(cached.promise);
          } else {
            var geometryPromise = void 0;

            if (primitive.extensions && primitive.extensions[EXTENSIONS.KHR_DRACO_MESH_COMPRESSION]) {
              // Use DRACO geometry if available
              geometryPromise = createDracoPrimitive(primitive);
            } else {
              // Otherwise create a new geometry
              geometryPromise = addPrimitiveAttributes(new THREE.BufferGeometry(), primitive, parser);
            } // Cache this geometry


            cache[cacheKey] = {
              primitive: primitive,
              promise: geometryPromise
            };
            pending.push(geometryPromise);
          }
        }

        return Promise.all(pending);
      }
      /**
       * Specification: https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/README.md#meshes
       * @param {number} meshIndex
       * @return {Promise<Group|Mesh|SkinnedMesh>}
       */

    }, {
      key: "loadMesh",
      value: function loadMesh(meshIndex) {
        var parser = this;
        var json = this.json;
        var extensions = this.extensions;
        var meshDef = json.meshes[meshIndex];
        var primitives = meshDef.primitives;
        var pending = [];

        for (var i = 0, il = primitives.length; i < il; i++) {
          var material = primitives[i].material === undefined ? createDefaultMaterial(this.cache) : this.getDependency('material', primitives[i].material);
          pending.push(material);
        }

        pending.push(parser.loadGeometries(primitives));
        return Promise.all(pending).then(function (results) {
          var materials = results.slice(0, results.length - 1);
          var geometries = results[results.length - 1];
          var meshes = [];

          for (var _i4 = 0, _il3 = geometries.length; _i4 < _il3; _i4++) {
            var geometry = geometries[_i4];
            var primitive = primitives[_i4]; // 1. create Mesh

            var mesh = void 0;
            var _material = materials[_i4];

            if (primitive.mode === WEBGL_CONSTANTS.TRIANGLES || primitive.mode === WEBGL_CONSTANTS.TRIANGLE_STRIP || primitive.mode === WEBGL_CONSTANTS.TRIANGLE_FAN || primitive.mode === undefined) {
              // .isSkinnedMesh isn't in glTF spec. See ._markDefs()
              mesh = meshDef.isSkinnedMesh === true ? new THREE.SkinnedMesh(geometry, _material) : new THREE.Mesh(geometry, _material);

              if (mesh.isSkinnedMesh === true && !mesh.geometry.attributes.skinWeight.normalized) {
                // we normalize floating point skin weight array to fix malformed assets (see #15319)
                // it's important to skip this for non-float32 data since normalizeSkinWeights assumes non-normalized inputs
                mesh.normalizeSkinWeights();
              }

              if (primitive.mode === WEBGL_CONSTANTS.TRIANGLE_STRIP) {
                mesh.geometry = toTrianglesDrawMode(mesh.geometry, THREE.TriangleStripDrawMode);
              } else if (primitive.mode === WEBGL_CONSTANTS.TRIANGLE_FAN) {
                mesh.geometry = toTrianglesDrawMode(mesh.geometry, THREE.TriangleFanDrawMode);
              }
            } else if (primitive.mode === WEBGL_CONSTANTS.LINES) {
              mesh = new THREE.LineSegments(geometry, _material);
            } else if (primitive.mode === WEBGL_CONSTANTS.LINE_STRIP) {
              mesh = new THREE.Line(geometry, _material);
            } else if (primitive.mode === WEBGL_CONSTANTS.LINE_LOOP) {
              mesh = new THREE.LineLoop(geometry, _material);
            } else if (primitive.mode === WEBGL_CONSTANTS.POINTS) {
              mesh = new THREE.Points(geometry, _material);
            } else {
              throw new Error('THREE.GLTFLoader: Primitive mode unsupported: ' + primitive.mode);
            }

            if (Object.keys(mesh.geometry.morphAttributes).length > 0) {
              updateMorphTargets(mesh, meshDef);
            }

            mesh.name = parser.createUniqueName(meshDef.name || 'mesh_' + meshIndex);
            assignExtrasToUserData(mesh, meshDef);
            if (primitive.extensions) addUnknownExtensionsToUserData(extensions, mesh, primitive);
            parser.assignFinalMaterial(mesh);
            meshes.push(mesh);
          }

          for (var _i5 = 0, _il4 = meshes.length; _i5 < _il4; _i5++) {
            parser.associations.set(meshes[_i5], {
              meshes: meshIndex,
              primitives: _i5
            });
          }

          if (meshes.length === 1) {
            return meshes[0];
          }

          var group = new THREE.Group();
          parser.associations.set(group, {
            meshes: meshIndex
          });

          for (var _i6 = 0, _il5 = meshes.length; _i6 < _il5; _i6++) {
            group.add(meshes[_i6]);
          }

          return group;
        });
      }
      /**
       * Specification: https://github.com/KhronosGroup/glTF/tree/master/specification/2.0#cameras
       * @param {number} cameraIndex
       * @return {Promise<THREE.Camera>}
       */

    }, {
      key: "loadCamera",
      value: function loadCamera(cameraIndex) {
        var camera;
        var cameraDef = this.json.cameras[cameraIndex];
        var params = cameraDef[cameraDef.type];

        if (!params) {
          console.warn('THREE.GLTFLoader: Missing camera parameters.');
          return;
        }

        if (cameraDef.type === 'perspective') {
          camera = new THREE.PerspectiveCamera(THREE.MathUtils.radToDeg(params.yfov), params.aspectRatio || 1, params.znear || 1, params.zfar || 2e6);
        } else if (cameraDef.type === 'orthographic') {
          camera = new THREE.OrthographicCamera(-params.xmag, params.xmag, params.ymag, -params.ymag, params.znear, params.zfar);
        }

        if (cameraDef.name) camera.name = this.createUniqueName(cameraDef.name);
        assignExtrasToUserData(camera, cameraDef);
        return Promise.resolve(camera);
      }
      /**
       * Specification: https://github.com/KhronosGroup/glTF/tree/master/specification/2.0#skins
       * @param {number} skinIndex
       * @return {Promise<Object>}
       */

    }, {
      key: "loadSkin",
      value: function loadSkin(skinIndex) {
        var skinDef = this.json.skins[skinIndex];
        var skinEntry = {
          joints: skinDef.joints
        };

        if (skinDef.inverseBindMatrices === undefined) {
          return Promise.resolve(skinEntry);
        }

        return this.getDependency('accessor', skinDef.inverseBindMatrices).then(function (accessor) {
          skinEntry.inverseBindMatrices = accessor;
          return skinEntry;
        });
      }
      /**
       * Specification: https://github.com/KhronosGroup/glTF/tree/master/specification/2.0#animations
       * @param {number} animationIndex
       * @return {Promise<AnimationClip>}
       */

    }, {
      key: "loadAnimation",
      value: function loadAnimation(animationIndex) {
        var json = this.json;
        var animationDef = json.animations[animationIndex];
        var pendingNodes = [];
        var pendingInputAccessors = [];
        var pendingOutputAccessors = [];
        var pendingSamplers = [];
        var pendingTargets = [];

        for (var i = 0, il = animationDef.channels.length; i < il; i++) {
          var channel = animationDef.channels[i];
          var sampler = animationDef.samplers[channel.sampler];
          var target = channel.target;
          var name = target.node !== undefined ? target.node : target.id; // NOTE: target.id is deprecated.

          var input = animationDef.parameters !== undefined ? animationDef.parameters[sampler.input] : sampler.input;
          var output = animationDef.parameters !== undefined ? animationDef.parameters[sampler.output] : sampler.output;
          pendingNodes.push(this.getDependency('node', name));
          pendingInputAccessors.push(this.getDependency('accessor', input));
          pendingOutputAccessors.push(this.getDependency('accessor', output));
          pendingSamplers.push(sampler);
          pendingTargets.push(target);
        }

        return Promise.all([Promise.all(pendingNodes), Promise.all(pendingInputAccessors), Promise.all(pendingOutputAccessors), Promise.all(pendingSamplers), Promise.all(pendingTargets)]).then(function (dependencies) {
          var nodes = dependencies[0];
          var inputAccessors = dependencies[1];
          var outputAccessors = dependencies[2];
          var samplers = dependencies[3];
          var targets = dependencies[4];
          var tracks = [];

          var _loop = function _loop(_i7, _il6) {
            var node = nodes[_i7];
            var inputAccessor = inputAccessors[_i7];
            var outputAccessor = outputAccessors[_i7];
            var sampler = samplers[_i7];
            var target = targets[_i7];
            if (node === undefined) return "continue";
            node.updateMatrix();
            node.matrixAutoUpdate = true;
            var TypedKeyframeTrack = void 0;

            switch (PATH_PROPERTIES[target.path]) {
              case PATH_PROPERTIES.weights:
                TypedKeyframeTrack = THREE.NumberKeyframeTrack;
                break;

              case PATH_PROPERTIES.rotation:
                TypedKeyframeTrack = THREE.QuaternionKeyframeTrack;
                break;

              case PATH_PROPERTIES.position:
              case PATH_PROPERTIES.scale:
              default:
                TypedKeyframeTrack = THREE.VectorKeyframeTrack;
                break;
            }

            var targetName = node.name ? node.name : node.uuid;
            var interpolation = sampler.interpolation !== undefined ? INTERPOLATION[sampler.interpolation] : THREE.InterpolateLinear;
            var targetNames = [];

            if (PATH_PROPERTIES[target.path] === PATH_PROPERTIES.weights) {
              node.traverse(function (object) {
                if (object.morphTargetInfluences) {
                  targetNames.push(object.name ? object.name : object.uuid);
                }
              });
            } else {
              targetNames.push(targetName);
            }

            var outputArray = outputAccessor.array;

            if (outputAccessor.normalized) {
              var scale = getNormalizedComponentScale(outputArray.constructor);
              var scaled = new Float32Array(outputArray.length);

              for (var j = 0, jl = outputArray.length; j < jl; j++) {
                scaled[j] = outputArray[j] * scale;
              }

              outputArray = scaled;
            }

            for (var _j = 0, _jl = targetNames.length; _j < _jl; _j++) {
              var track = new TypedKeyframeTrack(targetNames[_j] + '.' + PATH_PROPERTIES[target.path], inputAccessor.array, outputArray, interpolation); // Override interpolation with custom factory method.

              if (sampler.interpolation === 'CUBICSPLINE') {
                track.createInterpolant = function InterpolantFactoryMethodGLTFCubicSpline(result) {
                  // A CUBICSPLINE keyframe in glTF has three output values for each input value,
                  // representing inTangent, splineVertex, and outTangent. As a result, track.getValueSize()
                  // must be divided by three to get the interpolant's sampleSize argument.
                  var interpolantType = this instanceof THREE.QuaternionKeyframeTrack ? GLTFCubicSplineQuaternionInterpolant : GLTFCubicSplineInterpolant;
                  return new interpolantType(this.times, this.values, this.getValueSize() / 3, result);
                }; // Mark as CUBICSPLINE. `track.getInterpolation()` doesn't support custom interpolants.


                track.createInterpolant.isInterpolantFactoryMethodGLTFCubicSpline = true;
              }

              tracks.push(track);
            }
          };

          for (var _i7 = 0, _il6 = nodes.length; _i7 < _il6; _i7++) {
            var _ret = _loop(_i7);

            if (_ret === "continue") continue;
          }

          var name = animationDef.name ? animationDef.name : 'animation_' + animationIndex;
          return new THREE.AnimationClip(name, undefined, tracks);
        });
      }
    }, {
      key: "createNodeMesh",
      value: function createNodeMesh(nodeIndex) {
        var json = this.json;
        var parser = this;
        var nodeDef = json.nodes[nodeIndex];
        if (nodeDef.mesh === undefined) return null;
        return parser.getDependency('mesh', nodeDef.mesh).then(function (mesh) {
          var node = parser._getNodeRef(parser.meshCache, nodeDef.mesh, mesh); // if weights are provided on the node, override weights on the mesh.


          if (nodeDef.weights !== undefined) {
            node.traverse(function (o) {
              if (!o.isMesh) return;

              for (var i = 0, il = nodeDef.weights.length; i < il; i++) {
                o.morphTargetInfluences[i] = nodeDef.weights[i];
              }
            });
          }

          return node;
        });
      }
      /**
       * Specification: https://github.com/KhronosGroup/glTF/tree/master/specification/2.0#nodes-and-hierarchy
       * @param {number} nodeIndex
       * @return {Promise<Object3D>}
       */

    }, {
      key: "loadNode",
      value: function loadNode(nodeIndex) {
        var json = this.json;
        var extensions = this.extensions;
        var parser = this;
        var nodeDef = json.nodes[nodeIndex]; // reserve node's name before its dependencies, so the root has the intended name.

        var nodeName = nodeDef.name ? parser.createUniqueName(nodeDef.name) : '';
        return function () {
          var pending = [];

          var meshPromise = parser._invokeOne(function (ext) {
            return ext.createNodeMesh && ext.createNodeMesh(nodeIndex);
          });

          if (meshPromise) {
            pending.push(meshPromise);
          }

          if (nodeDef.camera !== undefined) {
            pending.push(parser.getDependency('camera', nodeDef.camera).then(function (camera) {
              return parser._getNodeRef(parser.cameraCache, nodeDef.camera, camera);
            }));
          }

          parser._invokeAll(function (ext) {
            return ext.createNodeAttachment && ext.createNodeAttachment(nodeIndex);
          }).forEach(function (promise) {
            pending.push(promise);
          });

          return Promise.all(pending);
        }().then(function (objects) {
          var node; // .isBone isn't in glTF spec. See ._markDefs

          if (nodeDef.isBone === true) {
            node = new THREE.Bone();
          } else if (objects.length > 1) {
            node = new THREE.Group();
          } else if (objects.length === 1) {
            node = objects[0];
          } else {
            node = new THREE.Object3D();
          }

          if (node !== objects[0]) {
            for (var i = 0, il = objects.length; i < il; i++) {
              node.add(objects[i]);
            }
          }

          if (nodeDef.name) {
            node.userData.name = nodeDef.name;
            node.name = nodeName;
          }

          assignExtrasToUserData(node, nodeDef);
          if (nodeDef.extensions) addUnknownExtensionsToUserData(extensions, node, nodeDef);

          if (nodeDef.matrix !== undefined) {
            var matrix = new THREE.Matrix4();
            matrix.fromArray(nodeDef.matrix);
            node.applyMatrix4(matrix);
          } else {
            if (nodeDef.translation !== undefined) {
              node.position.fromArray(nodeDef.translation);
            }

            if (nodeDef.rotation !== undefined) {
              node.quaternion.fromArray(nodeDef.rotation);
            }

            if (nodeDef.scale !== undefined) {
              node.scale.fromArray(nodeDef.scale);
            }
          }

          if (!parser.associations.has(node)) {
            parser.associations.set(node, {});
          }

          parser.associations.get(node).nodes = nodeIndex;
          return node;
        });
      }
      /**
       * Specification: https://github.com/KhronosGroup/glTF/tree/master/specification/2.0#scenes
       * @param {number} sceneIndex
       * @return {Promise<Group>}
       */

    }, {
      key: "loadScene",
      value: function loadScene(sceneIndex) {
        var json = this.json;
        var extensions = this.extensions;
        var sceneDef = this.json.scenes[sceneIndex];
        var parser = this; // Loader returns Group, not Scene.
        // See: https://github.com/mrdoob/three.js/issues/18342#issuecomment-578981172

        var scene = new THREE.Group();
        if (sceneDef.name) scene.name = parser.createUniqueName(sceneDef.name);
        assignExtrasToUserData(scene, sceneDef);
        if (sceneDef.extensions) addUnknownExtensionsToUserData(extensions, scene, sceneDef);
        var nodeIds = sceneDef.nodes || [];
        var pending = [];

        for (var i = 0, il = nodeIds.length; i < il; i++) {
          pending.push(buildNodeHierarchy(nodeIds[i], scene, json, parser));
        }

        return Promise.all(pending).then(function () {
          // Removes dangling associations, associations that reference a node that
          // didn't make it into the scene.
          var reduceAssociations = function reduceAssociations(node) {
            var reducedAssociations = new Map();

            var _iterator2 = _createForOfIteratorHelper(parser.associations),
                _step2;

            try {
              for (_iterator2.s(); !(_step2 = _iterator2.n()).done;) {
                var _step2$value = _slicedToArray(_step2.value, 2),
                    key = _step2$value[0],
                    value = _step2$value[1];

                if (key instanceof THREE.Material || key instanceof THREE.Texture) {
                  reducedAssociations.set(key, value);
                }
              }
            } catch (err) {
              _iterator2.e(err);
            } finally {
              _iterator2.f();
            }

            node.traverse(function (node) {
              var mappings = parser.associations.get(node);

              if (mappings != null) {
                reducedAssociations.set(node, mappings);
              }
            });
            return reducedAssociations;
          };

          parser.associations = reduceAssociations(scene);
          return scene;
        });
      }
    }]);

    return GLTFParser;
  }();

  function buildNodeHierarchy(nodeId, parentObject, json, parser) {
    var nodeDef = json.nodes[nodeId];
    return parser.getDependency('node', nodeId).then(function (node) {
      if (nodeDef.skin === undefined) return node; // build skeleton here as well

      var skinEntry;
      return parser.getDependency('skin', nodeDef.skin).then(function (skin) {
        skinEntry = skin;
        var pendingJoints = [];

        for (var i = 0, il = skinEntry.joints.length; i < il; i++) {
          pendingJoints.push(parser.getDependency('node', skinEntry.joints[i]));
        }

        return Promise.all(pendingJoints);
      }).then(function (jointNodes) {
        node.traverse(function (mesh) {
          if (!mesh.isMesh) return;
          var bones = [];
          var boneInverses = [];

          for (var j = 0, jl = jointNodes.length; j < jl; j++) {
            var jointNode = jointNodes[j];

            if (jointNode) {
              bones.push(jointNode);
              var mat = new THREE.Matrix4();

              if (skinEntry.inverseBindMatrices !== undefined) {
                mat.fromArray(skinEntry.inverseBindMatrices.array, j * 16);
              }

              boneInverses.push(mat);
            } else {
              console.warn('THREE.GLTFLoader: Joint "%s" could not be found.', skinEntry.joints[j]);
            }
          }

          mesh.bind(new THREE.Skeleton(bones, boneInverses), mesh.matrixWorld);
        });
        return node;
      });
    }).then(function (node) {
      // build node hierachy
      parentObject.add(node);
      var pending = [];

      if (nodeDef.children) {
        var children = nodeDef.children;

        for (var i = 0, il = children.length; i < il; i++) {
          var child = children[i];
          pending.push(buildNodeHierarchy(child, node, json, parser));
        }
      }

      return Promise.all(pending);
    });
  }
  /**
   * @param {BufferGeometry} geometry
   * @param {GLTF.Primitive} primitiveDef
   * @param {GLTFParser} parser
   */


  function computeBounds(geometry, primitiveDef, parser) {
    var attributes = primitiveDef.attributes;
    var box = new THREE.Box3();

    if (attributes.POSITION !== undefined) {
      var accessor = parser.json.accessors[attributes.POSITION];
      var min = accessor.min;
      var max = accessor.max; // glTF requires 'min' and 'max', but VRM (which extends glTF) currently ignores that requirement.

      if (min !== undefined && max !== undefined) {
        box.set(new THREE.Vector3(min[0], min[1], min[2]), new THREE.Vector3(max[0], max[1], max[2]));

        if (accessor.normalized) {
          var boxScale = getNormalizedComponentScale(WEBGL_COMPONENT_TYPES[accessor.componentType]);
          box.min.multiplyScalar(boxScale);
          box.max.multiplyScalar(boxScale);
        }
      } else {
        console.warn('THREE.GLTFLoader: Missing min/max properties for accessor POSITION.');
        return;
      }
    } else {
      return;
    }

    var targets = primitiveDef.targets;

    if (targets !== undefined) {
      var maxDisplacement = new THREE.Vector3();
      var vector = new THREE.Vector3();

      for (var i = 0, il = targets.length; i < il; i++) {
        var target = targets[i];

        if (target.POSITION !== undefined) {
          var _accessor = parser.json.accessors[target.POSITION];
          var _min = _accessor.min;
          var _max = _accessor.max; // glTF requires 'min' and 'max', but VRM (which extends glTF) currently ignores that requirement.

          if (_min !== undefined && _max !== undefined) {
            // we need to get max of absolute components because target weight is [-1,1]
            vector.setX(Math.max(Math.abs(_min[0]), Math.abs(_max[0])));
            vector.setY(Math.max(Math.abs(_min[1]), Math.abs(_max[1])));
            vector.setZ(Math.max(Math.abs(_min[2]), Math.abs(_max[2])));

            if (_accessor.normalized) {
              var _boxScale = getNormalizedComponentScale(WEBGL_COMPONENT_TYPES[_accessor.componentType]);

              vector.multiplyScalar(_boxScale);
            } // Note: this assumes that the sum of all weights is at most 1. This isn't quite correct - it's more conservative
            // to assume that each target can have a max weight of 1. However, for some use cases - notably, when morph targets
            // are used to implement key-frame animations and as such only two are active at a time - this results in very large
            // boxes. So for now we make a box that's sometimes a touch too small but is hopefully mostly of reasonable size.


            maxDisplacement.max(vector);
          } else {
            console.warn('THREE.GLTFLoader: Missing min/max properties for accessor POSITION.');
          }
        }
      } // As per comment above this box isn't conservative, but has a reasonable size for a very large number of morph targets.


      box.expandByVector(maxDisplacement);
    }

    geometry.boundingBox = box;
    var sphere = new THREE.Sphere();
    box.getCenter(sphere.center);
    sphere.radius = box.min.distanceTo(box.max) / 2;
    geometry.boundingSphere = sphere;
  }
  /**
   * @param {BufferGeometry} geometry
   * @param {GLTF.Primitive} primitiveDef
   * @param {GLTFParser} parser
   * @return {Promise<BufferGeometry>}
   */


  function addPrimitiveAttributes(geometry, primitiveDef, parser) {
    var attributes = primitiveDef.attributes;
    var pending = [];

    function assignAttributeAccessor(accessorIndex, attributeName) {
      return parser.getDependency('accessor', accessorIndex).then(function (accessor) {
        geometry.setAttribute(attributeName, accessor);
      });
    }

    for (var gltfAttributeName in attributes) {
      var threeAttributeName = ATTRIBUTES[gltfAttributeName] || gltfAttributeName.toLowerCase(); // Skip attributes already provided by e.g. Draco extension.

      if (threeAttributeName in geometry.attributes) continue;
      pending.push(assignAttributeAccessor(attributes[gltfAttributeName], threeAttributeName));
    }

    if (primitiveDef.indices !== undefined && !geometry.index) {
      var accessor = parser.getDependency('accessor', primitiveDef.indices).then(function (accessor) {
        geometry.setIndex(accessor);
      });
      pending.push(accessor);
    }

    assignExtrasToUserData(geometry, primitiveDef);
    computeBounds(geometry, primitiveDef, parser);
    return Promise.all(pending).then(function () {
      return primitiveDef.targets !== undefined ? addMorphTargets(geometry, primitiveDef.targets, parser) : geometry;
    });
  }
  /**
   * @param {BufferGeometry} geometry
   * @param {Number} drawMode
   * @return {BufferGeometry}
   */


  function toTrianglesDrawMode(geometry, drawMode) {
    var index = geometry.getIndex(); // generate index if not present

    if (index === null) {
      var indices = [];
      var position = geometry.getAttribute('position');

      if (position !== undefined) {
        for (var i = 0; i < position.count; i++) {
          indices.push(i);
        }

        geometry.setIndex(indices);
        index = geometry.getIndex();
      } else {
        console.error('THREE.GLTFLoader.toTrianglesDrawMode(): Undefined position attribute. Processing not possible.');
        return geometry;
      }
    } //


    var numberOfTriangles = index.count - 2;
    var newIndices = [];

    if (drawMode === THREE.TriangleFanDrawMode) {
      // gl.TRIANGLE_FAN
      for (var _i8 = 1; _i8 <= numberOfTriangles; _i8++) {
        newIndices.push(index.getX(0));
        newIndices.push(index.getX(_i8));
        newIndices.push(index.getX(_i8 + 1));
      }
    } else {
      // gl.TRIANGLE_STRIP
      for (var _i9 = 0; _i9 < numberOfTriangles; _i9++) {
        if (_i9 % 2 === 0) {
          newIndices.push(index.getX(_i9));
          newIndices.push(index.getX(_i9 + 1));
          newIndices.push(index.getX(_i9 + 2));
        } else {
          newIndices.push(index.getX(_i9 + 2));
          newIndices.push(index.getX(_i9 + 1));
          newIndices.push(index.getX(_i9));
        }
      }
    }

    if (newIndices.length / 3 !== numberOfTriangles) {
      console.error('THREE.GLTFLoader.toTrianglesDrawMode(): Unable to generate correct amount of triangles.');
    } // build final geometry


    var newGeometry = geometry.clone();
    newGeometry.setIndex(newIndices);
    return newGeometry;
  }

  /**
   * The Websocket Loading Manager is a custom Loading Manager that keeps track
   * of items that need to be loaded via the websocket server.
   *
   * Usually, when a loader fails to load an item, it marks it as done. This
   * manager handles that particular case: It doesn't mark the item as done
   * until it comes back from the websocket connection.
   *
   * Loading Managers handle and keep track of loaded and pending items.
   * For more information, see https://threejs.org/docs/#api/en/loaders/managers/LoadingManager
   */

  var WsLoadingManager = /*#__PURE__*/function (_LoadingManager) {
    _inherits(WsLoadingManager, _LoadingManager);

    var _super = _createSuper(WsLoadingManager);

    /**
     * Note: The onLoad, onProgress and onError methods have nothing to do with the Loader that has
     * this manager.
     *
     * @param onLoad Callback when all the items are loaded.
     * @param onProgress Callback when an item is loaded.
     * @param onError Callback when there is an error getting the item from the websocket server. See {@link markAsError}.
     */
    function WsLoadingManager(onLoad, onProgress, onError) {
      var _this;

      _classCallCheck(this, WsLoadingManager);

      _this = _super.call(this, onLoad, onProgress, onError);
      /**
       * Array of URLs that had an error related to the Loader.
       * This manager keeps track of these because we need to try to get them from the websocket server.
       */

      _this.errorItems = [];
      /**
       * The number of items loaded. Used to determine progress.
       */

      _this.itemsLoaded = 0;
      /**
       * The total number of items to load. Used to determine progress.
       */

      _this.itemsTotal = 0;
      /**
       * Determine whether items are being loaded or not.
       * Once the loaded items equal the total, we consider the loading to be done.
       */

      _this.isLoading = false;
      /**
       * itemStart method is called internally by loaders using this manager, whenever they start
       * getting the resource.
       */

      _this.itemStart = function (url) {
        _this.itemsTotal++;

        if (!_this.isLoading) {
          if (_this.onStart !== undefined) {
            _this.onStart(url, _this.itemsLoaded, _this.itemsTotal);
          }

          _this.isLoading = true;
        }
      };
      /**
       * itemEnd method is called internally by loaders using this manager, whenever they finish
       * loading the resource they where trying to load.
       *
       * This is called whether the resource had an error or not.
       */


      _this.itemEnd = function (url) {
        // This manager keeps track of the items that had errors. We don't want to mark them as done,
        // as they need to be get from the websocket server.
        if (_this.errorItems.includes(url)) {
          return;
        } // No error - Proceed to end the item.


        _this.itemsLoaded++;

        if (onProgress !== undefined) {
          onProgress(url, _this.itemsLoaded, _this.itemsTotal);
        }

        if (_this.itemsLoaded === _this.itemsTotal) {
          _this.isLoading = false;

          if (onLoad !== undefined) {
            onLoad();
          }
        }
      };
      /**
       * itemError method is called internally by loaders using this manager, whenever the resource
       * they are trying to load fails.
       */


      _this.itemError = function (url) {
        // This manager keeps track of the items that had errors. We don't want to mark them as error until we tried
        // getting the resource from the websocket server.
        if (!_this.errorItems.includes(url)) {
          _this.errorItems.push(url);

          return;
        }

        if (onError !== undefined) {
          onError(url);
        }
      };

      return _this;
    }
    /**
     * Mark an item as Done.
     * This method should be called manually when the websocket connection successfully gets the item.
     *
     * @param url The URL of the resource.
     */


    _createClass(WsLoadingManager, [{
      key: "markAsDone",
      value: function markAsDone(url) {
        if (this.errorItems.includes(url)) {
          this.filterAndEnd(url);
        }
      }
      /**
       * Mark an item as Error.
       * This method should be called manually when the websocket connection fails to get the item.
       *
       * @param url The URL of the resource.
       */

    }, {
      key: "markAsError",
      value: function markAsError(url) {
        if (this.errorItems.includes(url)) {
          this.itemError(url);
          this.filterAndEnd(url);
        }
      }
      /**
       * Internal method that removes an URL from the error items array and ends it.
       *
       * @param url The URL of the resource.
       */

    }, {
      key: "filterAndEnd",
      value: function filterAndEnd(url) {
        this.errorItems = this.errorItems.filter(function (errorUrl) {
          return errorUrl !== url;
        });
        this.itemEnd(url);
      }
    }]);

    return WsLoadingManager;
  }(THREE.LoadingManager);

  var JointTypes;

  (function (JointTypes) {
    JointTypes[JointTypes["REVOLUTE"] = 1] = "REVOLUTE";
    JointTypes[JointTypes["REVOLUTE2"] = 2] = "REVOLUTE2";
    JointTypes[JointTypes["PRISMATIC"] = 3] = "PRISMATIC";
    JointTypes[JointTypes["UNIVERSAL"] = 4] = "UNIVERSAL";
    JointTypes[JointTypes["BALL"] = 5] = "BALL";
    JointTypes[JointTypes["SCREW"] = 6] = "SCREW";
    JointTypes[JointTypes["GEARBOX"] = 7] = "GEARBOX";
    JointTypes[JointTypes["FIXED"] = 8] = "FIXED";
  })(JointTypes || (JointTypes = {}));
  /**
   * The scene is where everything is placed, from objects, to lights and cameras.
   *
   * Supports radial menu on an orthographic scene when gzradialmenu.js has been
   * included (useful for mobile devices).
   *
   * @param shaders Shaders instance, if not provided, custom shaders will
   *                not be set.
   * @param defaultCameraPosition THREE.Vector3 Default, and starting, camera
   *                              position. A value of [0, -5, 5] will be used
   *                              if this is undefined.
   * @param defaultCameraLookAt THREE.Vector3 Default, and starting, camera
   *                            lookAt position. A value of [0, 0, 0] will
   *                            be used if this is undefined.
   * @param backgroundColor THREE.Color The background color. A value of
   *                        0xb2b2b2 will be used if undefined.
   *
   * @param {function(resource)} findResourceCb - A function callback that can be used to help
   * @constructor
   */


  var Scene = /*#__PURE__*/function () {
    function Scene(config) {
      _classCallCheck(this, Scene);

      this.meshes = new Map();
      this.showCollisions = false;
      this.COMVisual = new THREE__namespace.Object3D();
      this.textureCache = new Map();
      this.currentThirdPersonLookAt = new THREE__namespace.Vector3();
      this.defaultThirdPersonCameraOffset = new THREE__namespace.Vector3(-6, -2, 1.5);
      this.currentThirdPersonCameraOffset = new THREE__namespace.Vector3();
      this.mousePointerDown = false;
      this.currentFirstPersonLookAt = new THREE__namespace.Vector3();
      /**
       * Create plane
       * @param {THREE.Vector3} normal
       * @param {double} width
       * @param {double} height
       * @returns {THREE.Mesh}
       */

      this.createPlane = function (normal, width, height) {
        // Create plane where width is along the x-axis and
        // and height along y-axi
        var geometry = new THREE__namespace.PlaneGeometry(width, height, 1, 1); // Manually specify the up vector to be along the z-axis since
        // the plane is created on XY plane

        var up = new THREE__namespace.Vector3(0, 0, 1);
        var material = new THREE__namespace.MeshPhongMaterial();
        var mesh = new THREE__namespace.Mesh(geometry, material); // Make sure the normal is normalized.

        normal = normal.normalize(); // Rotate the plane according to the normal.

        var axis = new THREE__namespace.Vector3();
        axis.crossVectors(up, normal);
        mesh.setRotationFromAxisAngle(axis, normal.angleTo(up));
        mesh.updateMatrix();
        mesh.name = "plane";
        mesh.receiveShadow = true;
        return mesh;
      };

      this.emitter = new eventemitter2.EventEmitter2({
        verboseMemoryLeak: true
      });
      this.shaders = config.shaders;

      if (config.findResourceCb) {
        this.findResourceCb = config.findResourceCb;
      } // This matches Gazebo's default camera position


      this.defaultCameraPosition = new THREE__namespace.Vector3(-6, 0, 6);

      if (config.defaultCameraPosition) {
        this.defaultCameraPosition.copy(config.defaultCameraPosition);
      }

      this.defaultCameraLookAt = new THREE__namespace.Vector3(0, 0, 0);

      if (config.defaultCameraLookAt) {
        this.defaultCameraLookAt.copy(config.defaultCameraLookAt);
      }

      this.backgroundColor = new THREE__namespace.Color(0xb2b2b2);

      if (config.backgroundColor) {
        this.backgroundColor.copy(config.backgroundColor);
      }

      this.init();
      /**
       * @member {string} selectEntity
       * The select entity event name.
       */

      this.selectEntityEvent = "select_entity";
      /**
       * @member {string} followEntity
       * The follow entity event name.
       */

      this.followEntityEvent = "follow_entity";
      /**
       * @member {string} moveToEntity
       * The move to entity event name.
       */

      this.moveToEntityEvent = "move_to_entity";
      /**
       * @member {string} thirdPersonFollowEntity
       * The third-person follow entity event name.
       */

      this.thirdPersonFollowEntityEvent = "third_person_follow_entity";
      /**
       * @member {string} firstPersonEntity
       * The first-person camera entity event name.
       */

      this.firstPersonEntityEvent = "first_person_entity";
      var that = this;
      /**
       * Handle entity selection signal ('select_entity').
       * @param {string} entityName The name of the entity to select.
       */

      this.emitter.on(this.selectEntityEvent, function (entityName) {
        var object = that.scene.getObjectByName(entityName);

        if (object !== undefined && object !== null) {
          that.selectEntity(object);
        }
      });
      /**
       * Handle the follow entity follow signal ('follow_entity').
       * @param {string} entityName Name of the entity. Pass in null or an empty
       * string to stop following.
       */

      this.emitter.on(this.followEntityEvent, function (entityName) {
        // Turn off following if `entity` is null.
        if (entityName === undefined || entityName === null) {
          that.cameraMode = "";
          return;
        }

        var object = that.scene.getObjectByName(entityName);

        if (object !== undefined && object !== null) {
          // Set the object to track.
          that.cameraTrackObject = object; // Set the camera mode.

          that.cameraMode = that.followEntityEvent;
        }
      });
      /**
       * Handle the third-person follow entity signal ('third_person_follow_entity').
       * @param {string} entityName Name of the entity. Pass in null or an empty
       * string to stop third-person following.
       */

      this.emitter.on(this.thirdPersonFollowEntityEvent, function (entityName) {
        // Turn off following if `entity` is null.
        if (entityName === undefined || entityName === null) {
          that.cameraMode = "";
          return;
        }

        var object = that.scene.getObjectByName(entityName);

        if (object !== undefined && object !== null) {
          // Set the object to track.
          that.cameraTrackObject = object; // Set the camera offset to the default one.

          that.currentThirdPersonCameraOffset.copy(that.defaultThirdPersonCameraOffset); // Set the camera mode.

          that.cameraMode = that.thirdPersonFollowEntityEvent;
        }
      });
      /**
       * Handle the first-person entity signal ('first_person_entity').
       * @param {string} entityName Name of the entity. Pass in null or an empty
       * string to stop first-person following.
       */

      this.emitter.on(this.firstPersonEntityEvent, function (entityName) {
        // Turn off following if `entity` is null.
        if (entityName === undefined || entityName === null) {
          that.cameraMode = "";
          return;
        }

        var object = that.scene.getObjectByName(entityName);

        if (object !== undefined && object !== null) {
          // Set the object to track.
          that.cameraTrackObject = object; // Set the camera mode.

          that.cameraMode = that.firstPersonEntityEvent;
        }
      });
      /**
       * Handle move to entity signal ('move_to_entity').
       * @param {string} entityName: Name of the entity.
       */

      this.emitter.on(this.moveToEntityEvent, function (entityName) {
        var obj = that.scene.getObjectByName(entityName);

        if (obj === undefined || obj === null) {
          return;
        } // Starting position of the camera.


        var startPos = new THREE__namespace.Vector3();
        that.camera.getWorldPosition(startPos); // Center of the target to move to.

        var targetCenter = new THREE__namespace.Vector3();
        obj.getWorldPosition(targetCenter); // Calculate  direction from start to target

        var dir = new THREE__namespace.Vector3();
        dir.subVectors(targetCenter, startPos);
        dir.normalize(); // Distance from start to target.

        var dist = startPos.distanceTo(targetCenter); // Get the bounding box size of the target object.

        var bboxSize = new THREE__namespace.Vector3();
        var bbox = new THREE__namespace.Box3().setFromObject(obj);
        bbox.getSize(bboxSize);
        var max = Math.max(bboxSize.x, bboxSize.y, bboxSize.z); // Compute an offset such that the object's bounding box will fix in the
        // view. I've padded this out a bit by multiplying `max` by 0.75 instead
        // of 0.5

        var offset = max * 0.75 / Math.tan(that.camera.fov * Math.PI / 180.0 / 2.0);
        var endPos = dir.clone().multiplyScalar(dist - offset);
        endPos.add(startPos); // Make sure that the end position is above the object so that the
        // camera will look down at it.

        if (endPos.z <= targetCenter.z + max) {
          endPos.z += max;
        } // Compute the end orientation.


        var endRotMat = new THREE__namespace.Matrix4();
        endRotMat.lookAt(endPos, targetCenter, new THREE__namespace.Vector3(0, 0, 1)); // Start the camera moving.

        that.cameraMode = that.moveToEntityEvent;
        that.cameraMoveToClock.start();
        that.cameraLerpStart.copy(startPos);
        that.cameraLerpEnd.copy(endPos);
        that.camera.getWorldQuaternion(that.cameraSlerpStart);
        that.cameraSlerpEnd.setFromRotationMatrix(endRotMat);
      });
    }
    /**
     * Initialize scene
     */


    _createClass(Scene, [{
      key: "init",
      value: function init() {
        var _this = this;

        THREE__namespace.Object3D.DefaultUp.set(0, 0, 1);
        this.name = "default";
        this.scene = new THREE__namespace.Scene(); // this.scene.name = this.name;
        // only support one heightmap for now.

        this.heightmap = null;
        this.selectedEntity = null;
        this.manipulationMode = "view";
        this.pointerOnMenu = false; // loaders

        this.textureLoader = new THREE__namespace.TextureLoader();
        this.textureLoader.crossOrigin = "";
        this.colladaLoader = new ColladaLoader();
        this.stlLoader = new STLLoader();
        this.gltfLoader = new GLTFLoader();
        this.ddsLoader = new DDSLoader(); // Progress and Load events.

        var progressEvent = function progressEvent(url, items, total) {
          _this.emitter.emit("load_progress", url, items, total);
        };

        var loadEvent = function loadEvent() {
          _this.emitter.emit("load_finished");
        }; // Set the right loading manager for handling websocket assets.


        if (this.findResourceCb) {
          var wsLoadingManager = new WsLoadingManager(loadEvent, progressEvent); // Collada Loader uses the findResourceCb internally.

          this.colladaLoader.findResourceCb = this.findResourceCb;
          this.textureLoader.manager = wsLoadingManager;
          this.colladaLoader.manager = wsLoadingManager;
          this.stlLoader.manager = wsLoadingManager;
          this.gltfLoader.manager = wsLoadingManager;
          this.ddsLoader.manager = wsLoadingManager;
        }

        this.textureLoader.manager.onProgress = progressEvent;
        this.colladaLoader.manager.onProgress = progressEvent;
        this.stlLoader.manager.onProgress = progressEvent;
        this.gltfLoader.manager.onProgress = progressEvent;
        this.ddsLoader.manager.onProgress = progressEvent;
        this.textureLoader.manager.onLoad = loadEvent;
        this.colladaLoader.manager.onLoad = loadEvent;
        this.stlLoader.manager.onLoad = loadEvent;
        this.gltfLoader.manager.onLoad = loadEvent;
        this.renderer = new THREE__namespace.WebGLRenderer({
          antialias: true
        });
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.setClearColor(this.backgroundColor);
        this.renderer.autoClear = false;
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE__namespace.PCFSoftShadowMap; // Particle group to render.
        // Add a default ambient value. This is equivalent to
        // {r: 0.1, g: 0.1, b: 0.1}.

        this.ambient = new THREE__namespace.AmbientLight(0x191919);
        this.scene.add(this.ambient); // camera

        var width = this.getDomElement().width;
        var height = this.getDomElement().height;
        this.camera = new THREE__namespace.PerspectiveCamera(60, width / height, 0.01, 1000);
        this.resetView(); // Clock used to time the camera 'move_to' motion.

        this.cameraMoveToClock = new THREE__namespace.Clock(false); // Start position of the camera's move_to

        this.cameraLerpStart = new THREE__namespace.Vector3(); // End position of the camera's move_to

        this.cameraLerpEnd = new THREE__namespace.Vector3(); // Start orientation of the camera's move_to

        this.cameraSlerpStart = new THREE__namespace.Quaternion(); // End orientation of the camera's move_to

        this.cameraSlerpEnd = new THREE__namespace.Quaternion(); // Current camera mode. Empty indicates standard orbit camera.

        this.cameraMode = ""; // Ortho camera and scene for rendering sprites
        // Currently only used for the radial menu

        /*if (typeof RadialMenu === 'function')
        {
          this.cameraOrtho = new THREE.OrthographicCamera(-width * 0.5, width * 0.5,
              height*0.5, -height*0.5, 1, 10);
          this.cameraOrtho.position.z = 10;
          this.sceneOrtho = new THREE.Scene();
               // Radial menu (only triggered by touch)
          // this.radialMenu = new RadialMenu(this.getDomElement());
          // this.sceneOrtho.add(this.radialMenu.menu);
        }*/
        // Grid

        this.grid = new THREE__namespace.GridHelper(20, 20, 0xcccccc, 0x4d4d4d);
        this.grid.name = "grid";
        this.grid.position.z = 0.05;
        this.grid.rotation.x = Math.PI * 0.5;
        this.grid.castShadow = false;
        this.grid.material.transparent = true;
        this.grid.material.opacity = 0.5;
        this.grid.visible = false;
        this.scene.add(this.grid);
        this.showCollisions = false;
        this.spawnModel = new SpawnModel(this, this.getDomElement());
        this.simpleShapesMaterial = new THREE__namespace.MeshPhongMaterial({
          color: 0xffffff,
          flatShading: false
        });
        var that = this; // Only capture events inside the webgl div element.

        this.getDomElement().addEventListener("mouseup", function (event) {
          that.onPointerUp(event);
        }, false);
        this.getDomElement().addEventListener("mousedown", function (event) {
          that.onPointerDown(event);
        }, false);
        this.getDomElement().addEventListener("wheel", function (event) {
          that.onMouseScroll(event);
        }, false);
        /*this.getDomElement().addEventListener( 'touchstart',
            function(event: TouchEvent) {that.onPointerDown(event);}, false );
             this.getDomElement().addEventListener( 'touchend',
            function(event: TouchEvent) {that.onPointerUp(event);}, false );
           */
        // Handles for translating and rotating objects
        //this.modelManipulator = new Manipulator(this.camera, false,
        //    this.getDomElement());
        // this.timeDown = null;
        // Create a ray caster

        this.ray = new THREE__namespace.Raycaster();
        this.controls = new OrbitControls(this.camera, this.getDomElement());
        this.controls.mouseButtons = {
          LEFT: THREE__namespace.MOUSE.ROTATE,
          MIDDLE: THREE__namespace.MOUSE.DOLLY,
          RIGHT: THREE__namespace.MOUSE.PAN
        }; // an animation loop is required with damping

        this.controls.enableDamping = false;
        this.controls.screenSpacePanning = true; // Bounding Box

        var indices = new Uint16Array([0, 1, 1, 2, 2, 3, 3, 0, 4, 5, 5, 6, 6, 7, 7, 4, 0, 4, 1, 5, 2, 6, 3, 7]);
        var positions = new Float32Array(8 * 3);
        var boxGeometry = new THREE__namespace.BufferGeometry();
        boxGeometry.setIndex(new THREE__namespace.BufferAttribute(indices, 1));
        boxGeometry.setAttribute("position", new THREE__namespace.BufferAttribute(positions, 3));
        this.boundingBox = new THREE__namespace.LineSegments(boxGeometry, new THREE__namespace.LineBasicMaterial({
          color: 0xffffff
        }));
        this.boundingBox.visible = false; // Joint visuals

        this.jointAxis = new THREE__namespace.Object3D();
        this.jointAxis.name = "JOINT_VISUAL";
        var geometry, material, mesh; // XYZ

        var XYZaxes = new THREE__namespace.Object3D();
        geometry = new THREE__namespace.CylinderGeometry(0.01, 0.01, 0.3, 10, 1, false);
        material = new THREE__namespace.MeshBasicMaterial({
          color: new THREE__namespace.Color(0xff0000)
        });
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.position.x = 0.15;
        mesh.rotation.z = -Math.PI / 2;
        mesh.name = "JOINT_VISUAL";
        XYZaxes.add(mesh);
        material = new THREE__namespace.MeshBasicMaterial({
          color: new THREE__namespace.Color(0x00ff00)
        });
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.position.y = 0.15;
        mesh.name = "JOINT_VISUAL";
        XYZaxes.add(mesh);
        material = new THREE__namespace.MeshBasicMaterial({
          color: new THREE__namespace.Color(0x0000ff)
        });
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.position.z = 0.15;
        mesh.rotation.x = Math.PI / 2;
        mesh.name = "JOINT_VISUAL";
        XYZaxes.add(mesh);
        geometry = new THREE__namespace.CylinderGeometry(0, 0.03, 0.1, 10, 1, true);
        material = new THREE__namespace.MeshBasicMaterial({
          color: new THREE__namespace.Color(0xff0000)
        });
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.position.x = 0.3;
        mesh.rotation.z = -Math.PI / 2;
        mesh.name = "JOINT_VISUAL";
        XYZaxes.add(mesh);
        material = new THREE__namespace.MeshBasicMaterial({
          color: new THREE__namespace.Color(0x00ff00)
        });
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.position.y = 0.3;
        mesh.name = "JOINT_VISUAL";
        XYZaxes.add(mesh);
        material = new THREE__namespace.MeshBasicMaterial({
          color: new THREE__namespace.Color(0x0000ff)
        });
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.position.z = 0.3;
        mesh.rotation.x = Math.PI / 2;
        mesh.name = "JOINT_VISUAL";
        XYZaxes.add(mesh);
        this.jointAxis["XYZaxes"] = XYZaxes;
        var mainAxis = new THREE__namespace.Object3D();
        material = new THREE__namespace.MeshLambertMaterial();
        material.color = new THREE__namespace.Color(0xffff00);
        var mainAxisLen = 0.3;
        geometry = new THREE__namespace.CylinderGeometry(0.015, 0.015, mainAxisLen, 36, 1, false);
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.position.z = mainAxisLen * 0.5;
        mesh.rotation.x = Math.PI / 2;
        mesh.name = "JOINT_VISUAL";
        mainAxis.add(mesh);
        geometry = new THREE__namespace.CylinderGeometry(0, 0.035, 0.1, 36, 1, false);
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.position.z = mainAxisLen;
        mesh.rotation.x = Math.PI / 2;
        mesh.name = "JOINT_VISUAL";
        mainAxis.add(mesh);
        this.jointAxis["mainAxis"] = mainAxis;
        var rotAxis = new THREE__namespace.Object3D();
        geometry = new THREE__namespace.TorusGeometry(0.04, 0.006, 10, 36, Math.PI * 3 / 2);
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.position.z = mainAxisLen;
        mesh.name = "JOINT_VISUAL";
        rotAxis.add(mesh);
        geometry = new THREE__namespace.CylinderGeometry(0.015, 0, 0.025, 10, 1, false);
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.position.y = -0.04;
        mesh.position.z = mainAxisLen;
        mesh.rotation.z = Math.PI / 2;
        mesh.name = "JOINT_VISUAL";
        rotAxis.add(mesh);
        this.jointAxis["rotAxis"] = rotAxis;
        var transAxis = new THREE__namespace.Object3D();
        geometry = new THREE__namespace.CylinderGeometry(0.01, 0.01, 0.1, 10, 1, true);
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.position.x = 0.03;
        mesh.position.y = 0.03;
        mesh.position.z = mainAxisLen * 0.5;
        mesh.rotation.x = Math.PI / 2;
        mesh.name = "JOINT_VISUAL";
        transAxis.add(mesh);
        geometry = new THREE__namespace.CylinderGeometry(0.02, 0, 0.0375, 10, 1, false);
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.position.x = 0.03;
        mesh.position.y = 0.03;
        mesh.position.z = mainAxisLen * 0.5 + 0.05;
        mesh.rotation.x = -Math.PI / 2;
        mesh.name = "JOINT_VISUAL";
        transAxis.add(mesh);
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.position.x = 0.03;
        mesh.position.y = 0.03;
        mesh.position.z = mainAxisLen * 0.5 - 0.05;
        mesh.rotation.x = Math.PI / 2;
        mesh.name = "JOINT_VISUAL";
        transAxis.add(mesh);
        this.jointAxis["transAxis"] = transAxis;
        var screwAxis = new THREE__namespace.Object3D();
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.position.x = -0.04;
        mesh.position.z = mainAxisLen - 0.11;
        mesh.rotation.z = -Math.PI / 4;
        mesh.rotation.x = -Math.PI / 10;
        mesh.name = "JOINT_VISUAL";
        screwAxis.add(mesh);
        var radius = 0.04;
        var length = 0.02;
        var curve = new THREE__namespace.CatmullRomCurve3([new THREE__namespace.Vector3(radius, 0, 0 * length), new THREE__namespace.Vector3(0, radius, 1 * length), new THREE__namespace.Vector3(-radius, 0, 2 * length), new THREE__namespace.Vector3(0, -radius, 3 * length), new THREE__namespace.Vector3(radius, 0, 4 * length), new THREE__namespace.Vector3(0, radius, 5 * length), new THREE__namespace.Vector3(-radius, 0, 6 * length)]);
        geometry = new THREE__namespace.TubeGeometry(curve, 36, 0.01, 10, false);
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.position.z = mainAxisLen - 0.23;
        mesh.name = "JOINT_VISUAL";
        screwAxis.add(mesh);
        this.jointAxis["screwAxis"] = screwAxis;
        var ballVisual = new THREE__namespace.Object3D();
        geometry = new THREE__namespace.SphereGeometry(0.06);
        mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.name = "JOINT_VISUAL";
        ballVisual.add(mesh);
        this.jointAxis["ballVisual"] = ballVisual; // center of mass visual

        this.COMvisual = new THREE__namespace.Object3D();
        this.COMvisual.name = "COM_VISUAL";
        geometry = new THREE__namespace.SphereGeometry(1, 32, 32);
        mesh = new THREE__namespace.Mesh(geometry); // \todo: This should be fixed to point to a correct material.

        /*this.setMaterial(mesh, {'ambient':[0.5,0.5,0.5,1.000000],
          'texture':'assets/media/materials/textures/com.png'});
          */

        mesh.name = "COM_VISUAL";
        mesh.rotation.z = -Math.PI / 2;
        this.COMvisual.add(mesh);
      }
    }, {
      key: "addSky",
      value: function addSky(cubemap) {
        var _this2 = this;

        if (cubemap === undefined) {
          var cubeLoader = new THREE__namespace.CubeTextureLoader();
          this.scene.background = cubeLoader.load(["https://fuel.gazebosim.org/1.0/openrobotics/models/skybox/tip/files/materials/textures/skybox-negx.jpg", "https://fuel.gazebosim.org/1.0/openrobotics/models/skybox/tip/files/materials/textures/skybox-posx.jpg", "https://fuel.gazebosim.org/1.0/openrobotics/models/skybox/tip/files/materials/textures/skybox-posy.jpg", "https://fuel.gazebosim.org/1.0/openrobotics/models/skybox/tip/files/materials/textures/skybox-negy.jpg", "https://fuel.gazebosim.org/1.0/openrobotics/models/skybox/tip/files/materials/textures/skybox-negz.jpg", "https://fuel.gazebosim.org/1.0/openrobotics/models/skybox/tip/files/materials/textures/skybox-posz.jpg"]);
        } else {
          this.ddsLoader.load(cubemap, // OnLoad callback that allows us to manipulate the texture.
          function (compressedTexture) {
            var images = [];
            var rawImages = compressedTexture.image; // Convert the binary data arrays to images

            for (var i = 0; i < rawImages.length; i++) {
              var image = rawImages[i]["mipmaps"][0];
              var imageElem = binaryToImage(image["data"], image["width"], image["height"]);
              images.push(imageElem);
            } // Reorder the images to support ThreeJS coordinate system.


            var reorderImages = [images[1], images[0], images[2], images[3], images[5], images[4]]; // Create the cube texture

            _this2.scene.background = new THREE__namespace.CubeTexture(reorderImages, compressedTexture.mapping, compressedTexture.wrapS, compressedTexture.wrapT, compressedTexture.magFilter, compressedTexture.minFilter, compressedTexture.format, compressedTexture.type, compressedTexture.anisotropy, compressedTexture.encoding);
            _this2.scene.background.needsUpdate = true;
          }, // OnProgress, do nothing
          function () {}, // OnError
          function (error) {
            if (_this2.findResourceCb) {
              // Get the mesh from the websocket server.
              _this2.findResourceCb(cubemap, function (material, error) {
                if (error !== undefined) {
                  // Mark the texture as error in the loading manager.
                  var _manager = _this2.ddsLoader.manager;

                  _manager.markAsError(cubemap);

                  return;
                } // Parse the DDS data.


                var texDatas = _this2.ddsLoader.parse(material.buffer.slice(material.byteOffset), true);

                var images = [];

                if (texDatas["isCubemap"]) {
                  var faces = texDatas["mipmaps"].length / texDatas["mipmapCount"];

                  for (var f = 0; f < faces; f++) {
                    for (var i = 0; i < texDatas["mipmapCount"]; i++) {
                      var data = texDatas["mipmaps"][f * texDatas["mipmapCount"] + i]["data"]; // Convert binary data to an image

                      var imageElem = binaryToImage(data, texDatas["width"], texDatas["height"]);
                      images.push(imageElem);
                    }
                  }
                } else {
                  console.error("Texture is not a cubemap. Sky will not be set."); // Mark the texture as error in the loading manager.

                  var _manager2 = _this2.ddsLoader.manager;

                  _manager2.markAsError(cubemap);

                  return;
                } // Reorder the images to support ThreeJS coordinate system.


                var reorderImages = [images[1], images[0], images[2], images[3], images[5], images[4]];
                _this2.scene.background = new THREE__namespace.CubeTexture(reorderImages);
                _this2.scene.background.format = texDatas["format"];

                if (texDatas["mipmapCount"] === 1) {
                  _this2.scene.background.minFilter = THREE__namespace.LinearFilter;
                }

                _this2.scene.background.needsUpdate = true; // Mark the texture as done in the loading manager.

                var manager = _this2.ddsLoader.manager;
                manager.markAsDone(cubemap);
              });
            }
          });
        }
      }
      /**
       * Add Fog to the scene.
       *
       * @param color Color can be a hexadecimal integer (recommended) or a CSS-style string.
       * @param density Defines how fast the fog will grow dense.
       * @param changeBackground Whether or not change the scene's background color accordingly.
       */

    }, {
      key: "addFog",
      value: function addFog(color, density, changeBackground) {
        this.scene.fog = new THREE__namespace.FogExp2(color, density);

        if (changeBackground === true) {
          this.scene.background = new THREE__namespace.Color(color);
        }
      }
    }, {
      key: "initScene",
      value: function initScene() {
        this.emitter.emit("show_grid", "show");
      }
    }, {
      key: "setSDFParser",
      value: function setSDFParser(sdfParser) {
        this.spawnModel.sdfParser = sdfParser;
      }
      /**
       * Window event callback
       * @param {} event - mousedown or touchdown events
       */

    }, {
      key: "onPointerDown",
      value: function onPointerDown(event) {
        event.preventDefault();
        this.mousePointerDown = true;

        if (this.spawnModel.active) {
          return;
        }

        var mainPointer = true;
        var pos;
        /*if (event.touches)
        {
          if (event.touches.length === 1)
          {
            pos = new THREE.Vector2(
                event.touches[0].clientX, event.touches[0].clientY);
          }
          else if (event.touches.length === 2)
          {
            pos = new THREE.Vector2(
                (event.touches[0].clientX + event.touches[1].clientX)/2,
                (event.touches[0].clientY + event.touches[1].clientY)/2);
          }
          else
          {
            return;
          }
        }
        else
        {*/

        pos = new THREE__namespace.Vector2(event.clientX, event.clientY);

        if (event.which !== 1) {
          mainPointer = false;
        } //}


        var intersect = new THREE__namespace.Vector3();
        var model = this.getRayCastModel(pos, intersect);

        if (intersect) {
          this.controls.target = intersect;
        } // Cancel in case of multitouch

        /*if (event.touches && event.touches.length !== 1)
        {
          return;
        }*/
        // Manipulation modes
        // Model found


        if (model) {
          // Do nothing to the floor plane
          if (model.name === "plane") ;
          /*else if (this.modelManipulator.pickerNames.indexOf(model.name) >= 0)
          {
            // Do not attach manipulator to itself
          }*/
          // Attach manipulator to model
          else if (model.name !== "") {
            if (mainPointer && model.parent === this.scene) ;
          } // Manipulator pickers, for mouse

          /*else if (this.modelManipulator.hovered)
          {
            this.modelManipulator.update();
            this.modelManipulator.object.updateMatrixWorld();
          }*/
          // Sky
          else ;
        }
      }
      /**
       * Window event callback
       * @param {} event - mouseup or touchend events
       */

    }, {
      key: "onPointerUp",
      value: function onPointerUp(event) {
        event.preventDefault();
        this.mousePointerDown = false;

        if (this.cameraMode === this.thirdPersonFollowEntityEvent) {
          // Calculate and store the new relative fixed camera position.
          // The offset we get in this.camera.position is in world coordinates,
          // but we want it relative to the object we are tracking.  Therefore,
          // do the inverse of what we do in render, namely:
          // 1. subtract the position of the tracked object
          // 2. Apply the inverse (conjugate) quaternion of the tracked object
          this.currentThirdPersonCameraOffset = this.camera.position.clone();
          this.currentThirdPersonCameraOffset.sub(this.cameraTrackObject.position);
          this.currentThirdPersonCameraOffset.applyQuaternion(this.cameraTrackObject.quaternion.conjugate());
        } // Clicks (<150ms) outside any models trigger view mode
        // var millisecs = new Date().getTime();

        /*if (millisecs - this.timeDown < 150)
        {
          this.setManipulationMode('view');
          // TODO: Remove jquery from scene
          if (typeof Gui === 'function')
          {
            $( '#view-mode' ).click();
            $('input[type="radio"]').checkboxradio('refresh');
          }
        }*/
        // this.timeDown = null;

      }
      /**
       * Window event callback
       * @param {} event - mousescroll event
       */

    }, {
      key: "onMouseScroll",
      value: function onMouseScroll(event) {
        event.preventDefault();
        var pos = new THREE__namespace.Vector2(event.clientX, event.clientY);
        var intersect = new THREE__namespace.Vector3();
        this.getRayCastModel(pos, intersect);

        if (intersect) {
          this.controls.target = intersect;
        }
      }
      /**
       * Window event callback
       * @param {} event - keydown events
       */

      /*public onKeyDown(event: MouseEvent): void {
        if (event.shiftKey)
        {
          // + and - for zooming
          if (event.keyCode === 187 || event.keyCode === 189)
          {
            var pos = new THREE.Vector2(this.getDomElement().width/2.0,
                this.getDomElement().height/2.0);
               var intersect = new THREE.Vector3();
            var model = this.getRayCastModel(pos, intersect);
               if (intersect)
            {
              this.controls.target = intersect;
            }
               if (event.keyCode === 187)
            {
              this.controls.dollyOut();
            }
            else
            {
              this.controls.dollyIn();
            }
          }
        }
           // DEL to delete entities
        if (event.keyCode === 46)
        {
          if (this.selectedEntity)
          {
            this.emitter.emit('delete_entity');
          }
        }
           // F2 for turning on effects
        if (event.keyCode === 113)
        {
          // this.effectsEnabled = !this.effectsEnabled;
        }
           // Esc/R/T for changing manipulation modes
        // TODO: Remove jquery from scene
        if (typeof Gui === 'function')
        {
          if (event.keyCode === 27) // Esc
          {
            $( '#view-mode' ).click();
            $('input[type="radio"]').checkboxradio('refresh');
          }
          if (event.keyCode === 82) // R
          {
            $( '#rotate-mode' ).click();
            $('input[type="radio"]').checkboxradio('refresh');
          }
          if (event.keyCode === 84) // T
          {
            $( '#translate-mode' ).click();
            $('input[type="radio"]').checkboxradio('refresh');
          }
        }
      }*/

      /**
       * Check if there's a model immediately under canvas coordinate 'pos'
       * @param {THREE.Vector2} pos - Canvas coordinates
       * @param {THREE.Vector3} intersect - Empty at input,
       * contains point of intersection in 3D world coordinates at output
       * @returns {THREE.Object3D} model - Intercepted model closest to the camera
       */

    }, {
      key: "getRayCastModel",
      value: function getRayCastModel(pos, intersect) {
        var rect = this.getDomElement().getBoundingClientRect();
        var vector = new THREE__namespace.Vector2((pos.x - rect.x) / rect.width * 2 - 1, -((pos.y - rect.y) / rect.height) * 2 + 1);
        this.ray.setFromCamera(vector, this.camera);
        var allObjects = [];
        getDescendants(this.scene, allObjects);
        var objects = this.ray.intersectObjects(allObjects);
        var model = new THREE__namespace.Object3D();
        var point;

        if (objects.length > 0) {
          for (var i = 0; i < objects.length; ++i) {
            model = objects[i].object;

            if (model.name.indexOf("_lightHelper") >= 0) {
              model = model.parent;
              break;
            }
            /*if (!this.modelManipulator.hovered &&
                (model.name === 'plane'))
            {
              // model = null;
              point = objects[i].point;
              break;
            }*/


            if (model.name === "grid" || model.name === "boundingBox" || model.name === "JOINT_VISUAL" || model.name === "INERTIA_VISUAL" || model.name === "COM_VISUAL") {
              point = objects[i].point;
              continue;
            }

            while (model.parent !== this.scene) {
              // Select current mode's handle

              /*if (model.parent.parent === this.modelManipulator.gizmo &&
                  ((this.manipulationMode === 'translate' &&
                    model.name.indexOf('T') >=0) ||
                   (this.manipulationMode === 'rotate' &&
                     model.name.indexOf('R') >=0)))
              {
                break modelsloop;
              }*/
              model = model.parent;
            }
            /*if (this.radialMenu && model === this.radialMenu.menu)
            {
              continue;
            }*/


            if (model.name.indexOf("COLLISION_VISUAL") >= 0) {
              continue;
            } else if (model.name !== "") {
              point = objects[i].point;
              break;
            }
          }
        }

        if (point) {
          intersect.x = point.x;
          intersect.y = point.y;
          intersect.z = point.z;
        }

        return model;
      }
      /**
       * Get the renderer's DOM element
       * @returns {domElement}
       */

    }, {
      key: "getDomElement",
      value: function getDomElement() {
        return this.renderer.domElement;
      }
      /**
       * Render scene
       */

    }, {
      key: "render",
      value: function render(timeElapsedMs) {
        // Kill camera control when:
        // -manipulating
        // -using radial menu
        // -pointer over menus
        // -spawning

        /* Disabling this for now so that mouse control stays enabled when the
         * mouse leaves the viewport.
         * if (this.modelManipulator.hovered ||
            (this.radialMenu && this.radialMenu.showing) ||
            this.pointerOnMenu ||
            this.spawnModel.active)
        {
          this.controls.enabled = false;
        }
        else
        {
          this.controls.enabled = true;
        }*/
        this.controls.update(); // If 'follow' mode, then track the specific object.

        if (this.cameraMode === this.followEntityEvent) {
          // Using a hard-coded offset for now.
          var relativeCameraOffset = new THREE__namespace.Vector3(-5, 0, 2);
          this.cameraTrackObject.updateMatrixWorld();
          var cameraOffset = relativeCameraOffset.applyMatrix4(this.cameraTrackObject.matrixWorld);
          this.camera.position.lerp(cameraOffset, 0.1);
          this.camera.lookAt(this.cameraTrackObject.position);
        } else if (this.cameraMode === this.thirdPersonFollowEntityEvent && !this.mousePointerDown) {
          // Based on https://discoverthreejs.com/book/first-steps/transformations/ ,
          // in THREE.js we have the following coordinate system:
          //
          // +X - Across the camera, to the right
          // -X - Across the camera, to the left
          // +Y - Up relative to the camera
          // -Y - Down relative to the camera
          // +Z - Towards the camera
          // -Z - Away from the camera
          var fixedCameraOffset = this.currentThirdPersonCameraOffset.clone();
          fixedCameraOffset.applyQuaternion(this.cameraTrackObject.quaternion);
          fixedCameraOffset.add(this.cameraTrackObject.position);
          var fixedLookAt = new THREE__namespace.Vector3(12, -4, 0);
          fixedLookAt.applyQuaternion(this.cameraTrackObject.quaternion);
          fixedLookAt.add(this.cameraTrackObject.position); // The calculation here comes from:
          // https://github.com/simondevyoutube/ThreeJS_Tutorial_ThirdPersonCamera/blob/main/main.js

          var timeElapsedSec = timeElapsedMs * 0.001;
          var timestep = 2.0 * timeElapsedSec;
          this.currentThirdPersonLookAt.lerp(fixedLookAt, timestep);
          this.camera.position.lerp(fixedCameraOffset, timestep);
          this.camera.lookAt(this.currentThirdPersonLookAt);
        } else if (this.cameraMode === this.firstPersonEntityEvent) {
          // Based on https://discoverthreejs.com/book/first-steps/transformations/ ,
          // in THREE.js we have the following coordinate system:
          //
          // +X - Across the camera, to the right
          // -X - Across the camera, to the left
          // +Y - Up relative to the camera
          // -Y - Down relative to the camera
          // +Z - Towards the camera
          // -Z - Away from the camera
          var _fixedCameraOffset = new THREE__namespace.Vector3(-0.12, 0, 0.6);

          _fixedCameraOffset.applyQuaternion(this.cameraTrackObject.quaternion);

          _fixedCameraOffset.add(this.cameraTrackObject.position);

          var _fixedLookAt = new THREE__namespace.Vector3(6, 0, 0);

          _fixedLookAt.applyQuaternion(this.cameraTrackObject.quaternion);

          _fixedLookAt.add(this.cameraTrackObject.position); // This is a pretty aggressive timestamp for lerping that makes the camera
          // bob a lot with the motion of the vehicle.  But I think it is what we want;
          // first-person camera should more-or-less feel like it is tied to the vehicle.


          var _timestep = 0.5;
          this.currentFirstPersonLookAt.lerp(_fixedLookAt, _timestep);
          this.camera.position.lerp(_fixedCameraOffset, _timestep);
          this.camera.lookAt(this.currentFirstPersonLookAt);
        } else if (this.cameraMode === this.moveToEntityEvent) {
          // Move the camera if "lerping" to an object.
          // Compute the lerp factor.
          var lerp = this.cameraMoveToClock.getElapsedTime() / 2.0; // Stop the clock if the camera has reached it's target
          //if (Math.abs(1.0 - lerp) <= 0.005) {

          if (lerp >= 1.0) {
            this.cameraMoveToClock.stop();
            this.cameraMode = "";
          } else {
            // Move the camera's position.
            this.camera.position.lerpVectors(this.cameraLerpStart, this.cameraLerpEnd, lerp); // Move the camera's orientation.

            THREE__namespace.Quaternion.slerp(this.cameraSlerpStart, this.cameraSlerpEnd, this.camera.quaternion, lerp);
          }
        } // this.modelManipulator.update();

        /*if (this.radialMenu)
        {
          this.radialMenu.update();
        }*/


        this.renderer.clear();
        this.renderer.render(this.scene, this.camera);
        this.renderer.clearDepth();

        if (this.sceneOrtho && this.cameraOrtho) {
          this.renderer.render(this.sceneOrtho, this.cameraOrtho);
        }
      }
      /**
       * Set scene size.
       * @param {double} width
       * @param {double} height
       */

    }, {
      key: "setSize",
      value: function setSize(width, height) {
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();

        if (this.cameraOrtho) {
          this.cameraOrtho.left = -width / 2;
          this.cameraOrtho.right = width / 2;
          this.cameraOrtho.top = height / 2;
          this.cameraOrtho.bottom = -height / 2;
          this.cameraOrtho.updateProjectionMatrix();
        }

        this.renderer.setSize(width, height);
        this.render(0);
      }
      /**
       * Add object to the scene
       * @param {THREE.Object3D} model
       */

    }, {
      key: "add",
      value: function add(model) {
        if (!model.userData) {
          model.userData = new ModelUserData();
        }

        this.scene.add(model);
      }
      /**
       * Remove object from the scene
       * @param {THREE.Object3D} model
       */

    }, {
      key: "remove",
      value: function remove(model) {
        this.scene.remove(model);
      }
      /**
       * Returns the object which has the given name
       * @param {string} name
       * @returns {THREE.Object3D} model
       */

    }, {
      key: "getByName",
      value: function getByName(name) {
        return this.scene.getObjectByName(name);
      }
      /**
       * Returns the object which has the given property value
       * @param {string} property name to search for
       * @param {string} value of the given property
       * @returns {THREE.Object3D} model
       */

    }, {
      key: "getByProperty",
      value: function getByProperty(property, value) {
        return this.scene.getObjectByProperty(property, value);
      }
      /**
       * Update a model's pose
       * @param {THREE.Object3D} model
       * @param {} position
       * @param {} orientation
       */

    }, {
      key: "updatePose",
      value: function updatePose(model, position, orientation) {
        /*if (this.modelManipulator && this.modelManipulator.object &&
            this.modelManipulator.hovered)
        {
          return;
        }*/
        this.setPose(model, position, orientation);
      }
      /**
       * Set a model's pose
       * @param {THREE.Object3D} model
       * @param {} position
       * @param {} orientation
       */

    }, {
      key: "setPose",
      value: function setPose(model, position, orientation) {
        model.position.x = position.x;
        model.position.y = position.y;
        model.position.z = position.z;
        model.quaternion.w = orientation.w;
        model.quaternion.x = orientation.x;
        model.quaternion.y = orientation.y;
        model.quaternion.z = orientation.z;
      }
    }, {
      key: "removeAll",
      value: function removeAll() {
        while (this.scene.children.length > 0) {
          this.scene.remove(this.scene.children[0]);
        }
      }
      /**
       * Create sphere
       * @param {double} radius
       * @returns {THREE.Mesh}
       */

    }, {
      key: "createSphere",
      value: function createSphere(radius) {
        var geometry = new THREE__namespace.SphereGeometry(radius, 32, 32);
        var mesh = new THREE__namespace.Mesh(geometry, this.simpleShapesMaterial);
        return mesh;
      }
      /**
       * Create cylinder
       * @param {double} radius
       * @param {double} length
       * @returns {THREE.Mesh}
       */

    }, {
      key: "createCylinder",
      value: function createCylinder(radius, length) {
        var geometry = new THREE__namespace.CylinderGeometry(radius, radius, length, 32, 1, false);
        var mesh = new THREE__namespace.Mesh(geometry, this.simpleShapesMaterial);
        mesh.rotation.x = Math.PI * 0.5;
        return mesh;
      }
      /**
       * Create capsule
       * @param {double} radius
       * @param {double} length
       * @returns {THREE.Mesh}
       */

    }, {
      key: "createCapsule",
      value: function createCapsule(radius, length) {
        var geometry = new THREE__namespace.CapsuleGeometry(radius, length, 32, 16);
        var mesh = new THREE__namespace.Mesh(geometry, this.simpleShapesMaterial);
        mesh.rotation.x = Math.PI * 0.5;
        return mesh;
      }
      /**
       * Create cone
       * @param {double} radius
       * @param {double} length
       * @returns {THREE.Mesh}
       */

    }, {
      key: "createCone",
      value: function createCone(radius, length) {
        var geometry = new THREE__namespace.ConeGeometry(radius, length, 32);
        var mesh = new THREE__namespace.Mesh(geometry, this.simpleShapesMaterial);
        mesh.rotation.x = Math.PI * 0.5;
        return mesh;
      }
      /**
       * Create ellipsoid
       * @param {double} radius
       * @param {double} length
       * @returns {THREE.Mesh}
       */

    }, {
      key: "createEllipsoid",
      value: function createEllipsoid(radius1, radius2, radius3) {
        var geometry = new THREE__namespace.SphereGeometry(radius1, 32, 32);
        geometry.scale(1, radius3 / radius1, radius2 / radius1);
        var mesh = new THREE__namespace.Mesh(geometry, this.simpleShapesMaterial);
        mesh.rotation.x = Math.PI * 0.5;
        return mesh;
      }
      /**
       * Create box
       * @param {double} width
       * @param {double} height
       * @param {double} depth
       * @returns {THREE.Mesh}
       */

    }, {
      key: "createBox",
      value: function createBox(width, height, depth) {
        var geometry = new THREE__namespace.BoxGeometry(width, height, depth, 1, 1, 1); // Fix UVs so textures are mapped in a way that is consistent to gazebo
        var uvAttribute = geometry.getAttribute("uv");
        /* THREEJS has moved away from faceVertexUvs to BufferGeometry attributes.
         * Need to migrate this code. See https://discourse.threejs.org/t/facevertexuvs-for-buffergeometry/23040
        for (var i = 0; i < faceUVFixA.length; ++i)
        {
          var idx = faceUVFixA[i]*2;
          // Make sure that the index is valid. A threejs box geometry may not
          // have all of the faces if a dimension is sufficiently small.
          if (idx + 1 < geometry.faceVertexUvs.length) {
            var uva = geometry.faceVertexUvs[0][idx][0];
            geometry.faceVertexUvs[0][idx][0] = geometry.faceVertexUvs[0][idx][1];
            geometry.faceVertexUvs[0][idx][1] = geometry.faceVertexUvs[0][idx+1][1];
            geometry.faceVertexUvs[0][idx][2] = uva;
                 geometry.faceVertexUvs[0][idx+1][0] = geometry.faceVertexUvs[0][idx+1][1];
            geometry.faceVertexUvs[0][idx+1][1] = geometry.faceVertexUvs[0][idx+1][2];
            geometry.faceVertexUvs[0][idx+1][2] = geometry.faceVertexUvs[0][idx][2];
          }
        }
        for (var ii = 0; ii < faceUVFixB.length; ++ii)
        {
          var idxB = faceUVFixB[ii]*2;
               // Make sure that the index is valid. A threejs box geometry may not
          // have all of the faces if a dimension is sufficiently small.
          if (idxB+1 < geometry.faceVertexUvs.length) {
            var uvc = geometry.faceVertexUvs[0][idxB][0];
            geometry.faceVertexUvs[0][idxB][0] = geometry.faceVertexUvs[0][idxB][2];
            geometry.faceVertexUvs[0][idxB][1] = uvc;
            geometry.faceVertexUvs[0][idxB][2] = geometry.faceVertexUvs[0][idxB+1][1];
                 geometry.faceVertexUvs[0][idxB+1][2] = geometry.faceVertexUvs[0][idxB][2];
            geometry.faceVertexUvs[0][idxB+1][1] = geometry.faceVertexUvs[0][idxB+1][0];
            geometry.faceVertexUvs[0][idxB+1][0] = geometry.faceVertexUvs[0][idxB][1];
          }
        }
        */

        uvAttribute.needsUpdate = true;
        var mesh = new THREE__namespace.Mesh(geometry, this.simpleShapesMaterial);
        mesh.castShadow = true;
        return mesh;
      }
      /**
       * Create light
       * @param {} type - 1: point, 2: spot, 3: directional
       * @param {} diffuse
       * @param {} intensity
       * @param {} pose
       * @param {} distance
       * @param {} cast_shadows
       * @param {} name
       * @param {} direction
       * @param {} specular
       * @param {} attenuation_constant
       * @param {} attenuation_linear
       * @param {} attenuation_quadratic
       * @returns {THREE.Object3D}
       */

    }, {
      key: "createLight",
      value: function createLight(type, diffuse, intensity, pose, distance, cast_shadows, name, direction, specular, attenuation_constant, attenuation_linear, attenuation_quadratic, inner_angle, outer_angle, falloff) {
        var obj = new THREE__namespace.Object3D();

        if (typeof diffuse === "undefined") {
          diffuse = new Color();
          diffuse.r = 1;
          diffuse.g = 1;
          diffuse.b = 1;
          diffuse.a = 1;
        }

        if (pose) {
          this.setPose(obj, pose.position, pose.orientation);
          obj.matrixWorldNeedsUpdate = true;
        }

        var lightObj;

        if (type === 1) {
          lightObj = this.createPointLight(obj, diffuse, intensity, distance, cast_shadows);
        } else if (type === 2) {
          lightObj = this.createSpotLight(obj, diffuse, intensity, distance, cast_shadows, inner_angle, outer_angle, falloff, direction);
        } else if (type === 3) {
          lightObj = this.createDirectionalLight(obj, diffuse, intensity, cast_shadows, direction);
        } else {
          console.error("Unknown light type", type);
          return obj;
        }

        if (name) {
          lightObj.name = name;
          obj.name = name;
        }

        obj.add(lightObj);
        return obj;
      }
      /**
       * Create point light - called by createLight
       * @param {} obj - light object
       * @param {} color
       * @param {} intensity
       * @param {} distance
       * @param {} cast_shadows
       * @returns {Object.<THREE.Light, THREE.Mesh>}
       */

    }, {
      key: "createPointLight",
      value: function createPointLight(obj, color, intensity, distance, cast_shadows) {
        if (typeof intensity === "undefined") {
          intensity = 0.5;
        }

        var lightObj = new THREE__namespace.PointLight(color, intensity);

        if (distance) {
          lightObj.distance = distance;
        }

        if (cast_shadows) {
          lightObj.castShadow = cast_shadows;
        }

        return lightObj;
      }
      /**
       * Create spot light - called by createLight
       * @param {} obj - light object
       * @param {} color
       * @param {} intensity
       * @param {} distance
       * @param {} cast_shadows
       * @returns {Object.<THREE.Light, THREE.Mesh>}
       */

    }, {
      key: "createSpotLight",
      value: function createSpotLight(obj, color, intensity, distance, cast_shadows, inner_angle, outer_angle, falloff, direction) {
        if (typeof intensity === "undefined") {
          intensity = 1;
        }

        if (typeof distance === "undefined") {
          distance = 20;
        }

        var lightObj = new THREE__namespace.SpotLight(color, intensity, distance);
        lightObj.position.set(0, 0, 0);

        if (inner_angle !== null && outer_angle !== null) {
          lightObj.angle = outer_angle;
          lightObj.penumbra = Math.max(1, (outer_angle - inner_angle) / ((inner_angle + outer_angle) / 2.0));
        }

        if (falloff !== null) {
          lightObj.decay = falloff;
        }

        if (cast_shadows) {
          lightObj.castShadow = cast_shadows;
        } // Set the target


        var dir = new THREE__namespace.Vector3(0, 0, -1);

        if (direction) {
          dir.x = direction.x;
          dir.y = direction.y;
          dir.z = direction.z;
        }

        var targetObj = new THREE__namespace.Object3D();
        lightObj.add(targetObj);
        targetObj.position.copy(dir);
        targetObj.matrixWorldNeedsUpdate = true;
        lightObj.target = targetObj;
        return lightObj;
      }
      /**
       * Create directional light - called by createLight
       * @param {} obj - light object
       * @param {} color
       * @param {} intensity
       * @param {} cast_shadows
       * @returns {Object.<THREE.Light, THREE.Mesh>}
       */

    }, {
      key: "createDirectionalLight",
      value: function createDirectionalLight(obj, color, intensity, cast_shadows, direction) {
        if (typeof intensity === "undefined") {
          intensity = 1;
        }

        var lightObj = new THREE__namespace.DirectionalLight(color, intensity);
        lightObj.shadow.camera.near = 1;
        lightObj.shadow.camera.far = 50;
        lightObj.shadow.mapSize.width = 4094;
        lightObj.shadow.mapSize.height = 4094;
        lightObj.shadow.camera.bottom = -100;
        lightObj.shadow.camera.right = 100;
        lightObj.shadow.camera.top = 100;
        lightObj.shadow.bias = 0.0001;
        lightObj.position.set(0, 0, 0);

        if (cast_shadows) {
          lightObj.castShadow = cast_shadows;
        } // Set the target


        var dir = new THREE__namespace.Vector3(0, 0, -1);

        if (direction) {
          dir.x = direction.x;
          dir.y = direction.y;
          dir.z = direction.z;
        }

        var targetObj = new THREE__namespace.Object3D();
        lightObj.add(targetObj);
        targetObj.position.copy(dir);
        targetObj.matrixWorldNeedsUpdate = true;
        lightObj.target = targetObj;
        return lightObj;
      }
      /**
       * Load heightmap
       * @param {} heights Lookup table of heights
       * @param {} width Width of the heightmap in meters
       * @param {} height Height of the heightmap in meters
       * @param {} segmentWidth Size of lookup table
       * @param {} segmentHeight Size of lookup table
       * @param {} origin Heightmap position in the world
       * @param {} textures
       * @param {} blends
       * @param {} parent
       */

    }, {
      key: "loadHeightmap",
      value: function loadHeightmap(heights, width, height, segmentWidth, segmentHeight, origin, textures, blends, parent) {
        if (this.heightmap) {
          console.error("Only one heightmap can be loaded at a time");
          return;
        }

        if (parent === undefined) {
          console.error("Missing parent, heightmap won't be loaded.");
          return;
        } // unfortunately large heightmaps kill the fps and freeze everything so
        // we have to scale it down


        var scale = 1;
        var maxHeightmapWidth = 256;

        if (segmentWidth - 1 > maxHeightmapWidth) {
          scale = maxHeightmapWidth / (segmentWidth - 1);
        }

        var geometry = new THREE__namespace.PlaneGeometry(width, height, (segmentWidth - 1) * scale, (segmentHeight - 1) * scale);
        var posAttribute = geometry.getAttribute("position"); // Sub-sample

        var col = (segmentWidth - 1) * scale;
        var row = (segmentHeight - 1) * scale;

        for (var r = 0; r < row; ++r) {
          for (var c = 0; c < col; ++c) {
            var index = r * col * 1 / (scale * scale) + c * (1 / scale);
            posAttribute.setZ(r * col + c, heights[index]);
          }
        }

        posAttribute.needsUpdate = true; // Compute normals

        geometry.normalizeNormals();
        geometry.computeVertexNormals();
        var material; // NOTE: Texture might be an array of textures, that need to blend in between.
        // For now, it only uses one texture.

        if (textures && textures.length > 0) {
          // Auxiliar method to configurate a texture's repeat and wrapping.
          var configTexture = function configTexture(texture, repeat) {
            texture.wrapS = THREE__namespace.RepeatWrapping;
            texture.wrapT = THREE__namespace.RepeatWrapping;
            texture.repeat.copy(repeat);
          };

          var texturesLoaded = [];
          var normalsLoaded = [];

          for (var t = 0; t < textures.length; ++t) {
            var diffuseUri = createFuelUri(textures[t].diffuse);
            texturesLoaded[t] = this.loadTexture(diffuseUri);
            configTexture(texturesLoaded[t], new THREE__namespace.Vector2(width / textures[t].size, height / textures[t].size));
            var normalUri = void 0;

            if (textures[t].normal) {
              normalUri = createFuelUri(textures[t].normal);
              normalsLoaded[t] = this.loadTexture(normalUri);
              configTexture(normalsLoaded[t], new THREE__namespace.Vector2(width / textures[t].size, height / textures[t].size));
            }
          }

          var materialOptions = {};

          if (texturesLoaded[0]) {
            materialOptions.map = texturesLoaded[0];
          }

          if (normalsLoaded[0]) {
            materialOptions.normalMap = normalsLoaded[0];
          }

          material = new THREE__namespace.MeshStandardMaterial(materialOptions);
        } else {
          material = new THREE__namespace.MeshPhongMaterial({
            color: 0x555555
          });
        }

        var mesh = new THREE__namespace.Mesh(geometry, material);
        mesh.receiveShadow = true;
        mesh.castShadow = false;
        mesh.position.x = origin.x;
        mesh.position.y = origin.y;
        mesh.position.z = origin.z;
        parent.add(mesh);
        this.heightmap = parent;
      }
      /**
       * Load mesh
       * @example
       * // loading using URI
       * // callback(mesh)
       * loadMeshFromUri('assets/house_1/meshes/house_1.dae', undefined, undefined, function(mesh)
                  {
                    // use the mesh
                  });
       * @param {string} uri
       * @param {} submesh
       * @param {} centerSubmesh
       * find a resource.
       * @param {function} onLoad
       * @param {function} onError
       */

    }, {
      key: "loadMeshFromUri",
      value: function loadMeshFromUri(uri, submesh, centerSubmesh, onLoad, onError) {
        uri.substring(0, uri.lastIndexOf("/"));
        var uriFile = uri.substring(uri.lastIndexOf("/") + 1); // Check if the mesh has already been loaded.
        // Use it in that case.

        if (this.meshes.has(uri)) {
          var mesh = this.meshes.get(uri).clone();

          if (submesh && this.useSubMesh(mesh, submesh, centerSubmesh)) {
            onLoad(mesh);
          } else if (!submesh) {
            onLoad(mesh);
          }

          return;
        } // load meshes


        if (uriFile.substr(-4).toLowerCase() === ".dae") {
          return this.loadCollada(uri, submesh, centerSubmesh, onLoad, onError);
        } else if (uriFile.substr(-4).toLowerCase() === ".obj") {
          return this.loadOBJ(uri, submesh, centerSubmesh, onLoad, onError);
        } else if (uriFile.substr(-4).toLowerCase() === ".stl") {
          return this.loadSTL(uri, submesh, centerSubmesh, onLoad, onError);
        } else if (uriFile.substr(-4).toLowerCase() === ".glb" || uriFile.substr(-5).toLowerCase() === ".gltf") {
          return this.loadGLTF(uri, submesh, centerSubmesh, onLoad, onError);
        } else if (uriFile.substr(-5).toLowerCase() === ".urdf") {
          console.error("Attempting to load URDF file, but it's not supported.");
        }
      }
      /**
       * Load mesh
       * @example
       * // loading using URI
       * // callback(mesh)
       * @example
       * // loading using file string
       * // callback(mesh)
       * loadMeshFromString('assets/house_1/meshes/house_1.dae', undefined, undefined, function(mesh)
                  {
                    // use the mesh
                  }, ['<?xml version="1.0" encoding="utf-8"?>
          <COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
            <asset>
              <contributor>
                <author>Cole</author>
                <authoring_tool>OpenCOLLADA for 3ds Max;  Ver.....']);
       * @param {string} uri
       * @param {} submesh
       * @param {} centerSubmesh
       * @param {function} onLoad
       * @param {function} onError
       * @param {array} files - files needed by the loaders[dae] in case of a collada
       * mesh, [obj, mtl] in case of object mesh, all as strings
       */

    }, {
      key: "loadMeshFromString",
      value: function loadMeshFromString(uri, submesh, centerSubmesh, onLoad, onError, files) {
        uri.substring(0, uri.lastIndexOf("/"));
        var uriFile = uri.substring(uri.lastIndexOf("/") + 1);

        if (this.meshes.has(uri)) {
          var mesh = this.meshes.get(uri).clone();

          if (submesh && this.useSubMesh(mesh, submesh, centerSubmesh)) {
            onLoad(mesh);
          } else if (!submesh) {
            onLoad(mesh);
          }

          return;
        } // load mesh


        if (uriFile.substr(-4).toLowerCase() === ".dae") {
          // loadCollada just accepts one file, which is the dae file as string
          if (files.length < 1 || !files[0]) {
            console.error("Missing DAE file");
            return;
          }

          this.loadCollada(uri, submesh, centerSubmesh, onLoad, onError, files[0]);
        } else if (uriFile.substr(-4).toLowerCase() === ".obj") {
          if (files.length < 2 || !files[0] || !files[1]) {
            console.error("Missing either OBJ or MTL file");
            return;
          }

          this.loadOBJ(uri, submesh, centerSubmesh, onLoad, onError, files);
        }
      }
      /**
       * Load collada file
       * @param {string} uri - mesh uri which is used by colldaloader to load
       * the mesh file using an XMLHttpRequest.
       * @param {} submesh
       * @param {} centerSubmesh
       * @param {function} onLoad - Callback when the mesh is loaded.
       * @param {function} onError - Callback when an error occurs.
       * @param {string} filestring -optional- the mesh file as a string to be
       * parsed
       * if provided the uri will not be used just as a url, no XMLHttpRequest will
       * be made.
       */

    }, {
      key: "loadCollada",
      value: function loadCollada(uri, submesh, centerSubmesh, onLoad, onError, filestring) {
        var _this3 = this;

        var dae;
        var that = this;
        /*
        // Crashes: issue #36
        if (this.meshes.has(uri))
        {
          dae = this.meshes.get(uri);
          dae = dae.clone();
          this.useColladaSubMesh(dae, submesh, centerSubmesh);
          onLoad(dae);
          return;
        }
        */

        function meshReady(collada) {
          // check for a scale factor

          /*if(collada.dae.asset.unit)
          {
            var scale = collada.dae.asset.unit;
            collada.scene.scale = new THREE.Vector3(scale, scale, scale);
          }*/
          dae = collada.scene;
          dae.updateMatrix();
          that.prepareColladaMesh(dae);
          that.meshes.set(uri, dae);
          dae = dae.clone();
          dae.name = uri;

          if (submesh && that.useSubMesh(dae, submesh, centerSubmesh)) {
            onLoad(dae);
          } else if (!submesh) {
            onLoad(dae);
          }
        }

        if (!filestring) {
          this.colladaLoader.load(uri, // onLoad callback
          function (collada) {
            meshReady(collada);
          }, // onProgress callback
          function (progress) {}, // onError callback
          function (error) {
            if (_this3.findResourceCb) {
              // Get the mesh from the websocket server.
              _this3.findResourceCb(uri, function (mesh, error) {
                if (error !== undefined) {
                  // Mark the mesh as error in the loading manager.
                  var _manager3 = _this3.colladaLoader.manager;

                  _manager3.markAsError(uri);

                  return;
                }

                meshReady(_this3.colladaLoader.parse(new TextDecoder().decode(mesh), uri)); // Mark the mesh as done in the loading manager.

                var manager = _this3.colladaLoader.manager;
                manager.markAsDone(uri);
              });
            }
          });
        } else {
          meshReady(this.colladaLoader.parse(filestring, undefined));
        }
      }
      /**
       * Prepare collada by removing other non-mesh entities such as lights
       * @param {} dae
       */

    }, {
      key: "prepareColladaMesh",
      value: function prepareColladaMesh(dae) {
        var allChildren = [];
        getDescendants(dae, allChildren);

        for (var i = 0; i < allChildren.length; ++i) {
          if (allChildren[1] && allChildren[i] instanceof THREE__namespace.Light && allChildren[i].parent) {
            allChildren[i].parent.remove(allChildren[i]);
          }
        }
      }
      /**
       * Prepare mesh by handling submesh-only loading
       * @param {THREE.Mesh} mesh
       * @param {} submesh
       * @param {} centerSubmesh
       * @returns {THREE.Mesh} mesh
       */

    }, {
      key: "useSubMesh",
      value: function useSubMesh(mesh, submesh, centerSubmesh) {
        if (!submesh) {
          return null;
        }
        // meshes or groups that contain meshes. We need to modify the mesh, so
        // only the required submesh is contained in it. Note: If a submesh is
        // contained in a group, we need to preserve that group, as it may apply
        // matrix transformations required by the submesh.
        // Auxiliary function used to look for the required submesh.
        // Checks if the given submesh is the one we look for. If it's a Group, look for it within its children.
        // It returns the submesh, if found.

        function lookForSubmesh(obj, parent) {
          if (obj instanceof THREE__namespace.Mesh) {
            // Check if the mesh has the correct name and has geometry.
            if (obj.name === submesh && obj.hasOwnProperty("geometry")) {
              // Center the submesh.
              if (centerSubmesh) {
                // obj file
                if (obj.geometry instanceof THREE__namespace.BufferGeometry) {
                  var geomPosition = obj.geometry.getAttribute("position");
                  var minPos = new THREE__namespace.Vector3();
                  var maxPos = new THREE__namespace.Vector3();
                  var centerPos = new THREE__namespace.Vector3();
                  minPos.fromBufferAttribute(geomPosition, 0);
                  maxPos.fromBufferAttribute(geomPosition, 0); // Get the min and max values.

                  for (var _i = 0; _i < geomPosition.count; _i++) {
                    minPos.x = Math.min(minPos.x, geomPosition.getX(_i));
                    minPos.y = Math.min(minPos.y, geomPosition.getY(_i));
                    minPos.z = Math.min(minPos.z, geomPosition.getZ(_i));
                    maxPos.x = Math.max(maxPos.x, geomPosition.getX(_i));
                    maxPos.y = Math.max(maxPos.y, geomPosition.getY(_i));
                    maxPos.z = Math.max(maxPos.z, geomPosition.getZ(_i));
                  } // Compute center position


                  centerPos = minPos.add(maxPos.sub(minPos).multiplyScalar(0.5)); // Update geometry position

                  for (var _i2 = 0; _i2 < geomPosition.count; _i2++) {
                    var origPos = new THREE__namespace.Vector3();
                    origPos.fromBufferAttribute(geomPosition, _i2);
                    var newPos = origPos.sub(centerPos);
                    geomPosition.setXYZ(_i2, newPos.x, newPos.y, newPos.z);
                  }

                  geomPosition.needsUpdate = true; // Center the position.

                  obj.position.set(0, 0, 0);
                  var childParent = obj.parent;

                  while (childParent) {
                    childParent.position.set(0, 0, 0);
                    childParent = childParent.parent;
                  }
                }
              } // Filter the children of the parent. Only the required submesh
              // needs to be there.


              parent.children = [obj];
              return [true, obj];
            }
          } else {
            for (var _i3 = 0; _i3 < obj.children.length; _i3++) {
              if (obj.children[_i3] instanceof THREE__namespace.Mesh || obj.children[_i3] instanceof THREE__namespace.Group) {
                var _lookForSubmesh = lookForSubmesh(obj.children[_i3], obj),
                    _lookForSubmesh2 = _slicedToArray(_lookForSubmesh, 2),
                    found = _lookForSubmesh2[0],
                    _result = _lookForSubmesh2[1];

                if (found) {
                  // This keeps the Group (obj), and modifies it's children to
                  // contain only the submesh.
                  obj.children = [_result];
                  return [true, obj];
                }
              }
            }
          }

          return [false, obj];
        } // Look for the submesh in the children of the mesh.


        for (var i = 0; i < mesh.children.length; i++) {
          if (mesh.children[i] instanceof THREE__namespace.Mesh || mesh.children[i] instanceof THREE__namespace.Group) {
            var _lookForSubmesh3 = lookForSubmesh(mesh.children[i], mesh),
                _lookForSubmesh4 = _slicedToArray(_lookForSubmesh3, 2),
                found = _lookForSubmesh4[0],
                _result2 = _lookForSubmesh4[1];

            if (found) {
              return _result2;
            }
          }
        }

        return null;
      }
      /**
       * Load obj file.
       * Loads obj mesh given using it's uri
       * @param {string} uri
       * @param {} submesh
       * @param {} centerSubmesh
       * @param {function} onLoad
       * @param {function} onError
       */

    }, {
      key: "loadOBJ",
      value: function loadOBJ(uri, submesh, centerSubmesh, onLoad, onError, files) {
        var objLoader = new GzObjLoader(this, uri, submesh, centerSubmesh, this.findResourceCb, onLoad, onError, files);
        objLoader.load();
      }
      /**
       * Load stl file.
       * Loads stl mesh given using it's uri
       * @param {string} uri
       * @param {} submesh
       * @param {} centerSubmesh
       * @param {function} onLoad
       */

    }, {
      key: "loadSTL",
      value: function loadSTL(uri, submesh, centerSubmesh, onLoad, onError) {
        var mesh = null;
        var that = this;
        this.stlLoader.load(uri, // onLoad
        function (geometry) {
          mesh = new THREE__namespace.Mesh(geometry);
          mesh.castShadow = true;
          mesh.receiveShadow = true;
          that.meshes.set(uri, mesh);
          mesh = mesh.clone();
          mesh.name = uri;

          if (submesh && that.useSubMesh(mesh, submesh, centerSubmesh)) {
            onLoad(mesh);
          } else if (!submesh) {
            onLoad(mesh);
          }
        }, // onProgress
        function (progress) {}, // onError
        function (error) {
          if (that.findResourceCb) {
            // Get the mesh from the websocket server.
            that.findResourceCb(uri, function (rawmesh, error) {
              if (error !== undefined) {
                // Mark the mesh as error in the loading manager.
                var _manager4 = that.stlLoader.manager;

                _manager4.markAsError(uri);

                return;
              }

              var decoded = that.stlLoader.parse(rawmesh);
              decoded.name = uri;
              onLoad(decoded); // Mark the mesh as done in the loading manager.

              var manager = that.stlLoader.manager;
              manager.markAsDone(uri);
            });
          }
        });
      }
      /**
       * Load GLTF/GLB file
       * @param {string} uri
       * @param {} submesh
       * @param {} centerSubmesh
       * @param {function} onLoad - Callback when the mesh is loaded.
       * @param {function} onError - Callback when an error occurs.
       */

    }, {
      key: "loadGLTF",
      value: function loadGLTF(uri, submesh, centerSubmesh, onLoad, onError) {
        var _this4 = this;

        var that = this;
        this.gltfLoader.load(uri, // onLoad callback
        function (gltf) {
          var mesh = gltf.scene;
          mesh.name = uri;

          if (submesh && that.useSubMesh(mesh, submesh, centerSubmesh)) {
            onLoad(mesh);
          } else if (!submesh) {
            onLoad(mesh);
          }
        }, // onProgress callback
        function (progress) {}, // onError callback
        function (error) {
          if (_this4.findResourceCb) {
            // Get the mesh from the websocket server.
            _this4.findResourceCb(uri, function (data, error) {
              if (error !== undefined) {
                // Mark the mesh as error in the loading manager.
                var manager = _this4.gltfLoader.manager;
                manager.markAsError(uri);
                return;
              } // The GLTFLoader expects an ArrayBuffer for binary data (GLB files).
              // However, the data received might be a Uint8Array or even a string depending on the transport.
              // We need to detect if it's a binary GLB file (starts with "glTF" magic bytes) and convert it
              // to a clean ArrayBuffer if necessary.


              var resourceContent = data;
              var isGLB = false; // Check for GLB binary header "glTF" (0x67 0x6C 0x54 0x46)

              if (typeof data === "string" && data.startsWith("glTF")) {
                isGLB = true;
              } else if (data instanceof Uint8Array && data.length >= 4) {
                if (data[0] === 0x67 && data[1] === 0x6c && data[2] === 0x54 && data[3] === 0x46) {
                  isGLB = true;
                }
              } else if (data instanceof ArrayBuffer && data.byteLength >= 4) {
                var header = new Uint8Array(data, 0, 4);

                if (header[0] === 0x67 && header[1] === 0x6c && header[2] === 0x54 && header[3] === 0x46) {
                  isGLB = true;
                }
              } // If it is a GLB file but in string format (e.g. from some websocket frames),
              // convert the string to an ArrayBuffer.


              if (isGLB && typeof data === "string") {
                var len = data.length;
                var array = new Uint8Array(len);

                for (var i = 0; i < len; i++) {
                  array[i] = data.charCodeAt(i);
                }

                resourceContent = array.buffer;
              } else if (data instanceof Uint8Array) {
                // If it's a Uint8Array, use slice().buffer to get a fresh ArrayBuffer view
                // of just the data we need, without any offset issues.
                resourceContent = data.slice().buffer;
              }

              _this4.gltfLoader.parse(resourceContent, uri, function (gltf) {
                var mesh = gltf.scene;
                mesh.name = uri;

                if (submesh && that.useSubMesh(mesh, submesh, centerSubmesh)) {
                  onLoad(mesh);
                } else if (!submesh) {
                  onLoad(mesh);
                } // Mark the mesh as done in the loading manager.


                var manager = _this4.gltfLoader.manager;
                manager.markAsDone(uri);
              }, function (error) {
                console.error("Error parsing GLTF from websocket", error);
                var manager = _this4.gltfLoader.manager;
                manager.markAsError(uri);
              });
            });
          }
        });
      }
      /**
       * Set material for an object
       * @param {} obj
       * @param {} material
       */

    }, {
      key: "setMaterial",
      value: function setMaterial(obj, material) {

        if (obj) {
          if (material) {
            // If the material has a PBR tag, use a MeshStandardMaterial,
            // which can have albedo, normal, emissive, roughness and metalness
            // maps. Otherwise use a Phong material.
            if (material.pbr) {
              obj.material = new THREE__namespace.MeshStandardMaterial(); // Array of maps in order to facilitate the repetition and scaling process.

              var maps = [];

              if (material.pbr.albedoMap) {
                var albedoMap = this.loadTexture(material.pbr.albedoMap);
                obj.material.map = albedoMap;
                maps.push(albedoMap); // enable alpha test for textures with alpha transparency

                if (albedoMap.format === THREE__namespace.RGBAFormat) {
                  obj.material.alphaTest = 0.5;
                }
              }

              if (material.pbr.normalMap) {
                var normalMap = this.loadTexture(material.pbr.normalMap);
                obj.material.normalMap = normalMap;
                maps.push(normalMap);
              }

              if (material.pbr.emissiveMap) {
                var emissiveMap = this.loadTexture(material.pbr.emissiveMap);
                obj.material.emissiveMap = emissiveMap;
                maps.push(emissiveMap);
              }

              if (material.pbr.roughnessMap) {
                var roughnessMap = this.loadTexture(material.pbr.roughnessMap);
                obj.material.roughnessMap = roughnessMap;
                maps.push(roughnessMap);
              }

              if (material.pbr.metalnessMap) {
                var metalnessMap = this.loadTexture(material.pbr.metalnessMap);
                obj.material.metalnessMap = metalnessMap;
                maps.push(metalnessMap);
              }

              maps.forEach(function (map) {
                map.wrapS = map.wrapT = THREE__namespace.RepeatWrapping;
                map.repeat.x = 1.0;
                map.repeat.y = 1.0;

                if (material.scale) {
                  map.repeat.x = 1.0 / material.scale[0];
                  map.repeat.y = 1.0 / material.scale[1];
                }
              });
            } else {
              obj.material = new THREE__namespace.MeshPhongMaterial();
              var specular = material.specular;

              if (specular) {
                obj.material.specular.copy(specular);
              }

              if (material.texture) {
                var texture = this.loadTexture(material.texture);
                texture.wrapS = texture.wrapT = THREE__namespace.RepeatWrapping;
                texture.repeat.x = 1.0;
                texture.repeat.y = 1.0;

                if (material.scale) {
                  texture.repeat.x = 1.0 / material.scale[0];
                  texture.repeat.y = 1.0 / material.scale[1];
                }

                obj.material.map = texture; // enable alpha test for textures with alpha transparency

                if (texture.format === THREE__namespace.RGBAFormat) {
                  obj.material.alphaTest = 0.5;
                }
              }

              if (material.normalMap) {
                obj.material.normalMap = this.loadTexture(material.normalMap);
              }
            }

            var ambient = material.ambient;
            var diffuse = material.diffuse;

            if (diffuse) {
              // threejs removed ambient from phong and lambert materials so
              // aproximate the resulting color by mixing ambient and diffuse
              var dc = [];
              dc[0] = diffuse.r;
              dc[1] = diffuse.g;
              dc[2] = diffuse.b;

              if (ambient) {
                var a = 0.4;
                var d = 0.6;
                dc[0] = ambient.r * a + diffuse.r * d;
                dc[1] = ambient.g * a + diffuse.g * d;
                dc[2] = ambient.b * a + diffuse.b * d;
              }

              obj.material.color.setRGB(dc[0], dc[1], dc[2]);
            }

            var opacity = material.opacity;

            if (opacity) {
              if (opacity < 1) {
                obj.material.transparent = true;
                obj.material.opacity = opacity;
              }
            }
          }
        }
      }
      /**
       * Set manipulation mode (view/translate/rotate)
       * @param {string} mode
       */

    }, {
      key: "setManipulationMode",
      value: function setManipulationMode(mode) {
        this.manipulationMode = mode;

        if (mode === "view") {
          /*if (this.modelManipulator.object)
          {
            this.emitter.emit('entityChanged', this.modelManipulator.object);
          }*/
          this.selectEntity(null);
        } else {
          // Toggle manipulaion space (world / local)

          /*if (this.modelManipulator.mode === this.manipulationMode)
          {
            this.modelManipulator.space =
              (this.modelManipulator.space === 'world') ? 'local' : 'world';
          }
          this.modelManipulator.mode = this.manipulationMode;
          this.modelManipulator.setMode(this.modelManipulator.mode);
          */
          // model was selected during view mode
          if (this.selectedEntity) {
            this.selectEntity(this.selectedEntity);
          }
        }
      }
      /**
       * Show collision visuals
       * @param {boolean} show
       */

    }, {
      key: "showCollision",
      value: function showCollision(show) {
        if (show === this.showCollisions) {
          return;
        }

        var allObjects = [];
        getDescendants(this.scene, allObjects);

        for (var i = 0; i < allObjects.length; ++i) {
          if (allObjects[i] instanceof THREE__namespace.Object3D && allObjects[i].name.indexOf("COLLISION_VISUAL") >= 0) {
            var allChildren = [];
            getDescendants(allObjects[i], allChildren);

            for (var j = 0; j < allChildren.length; ++j) {
              if (allChildren[j] instanceof THREE__namespace.Mesh) {
                allChildren[j].visible = show;
              }
            }
          }
        }

        this.showCollisions = show;
      }
      /**
       * Attach manipulator to an object
       * @param {THREE.Object3D} model
       * @param {string} mode (translate/rotate)
       */

    }, {
      key: "attachManipulator",
      value: function attachManipulator(model, mode) {
        /*if (this.modelManipulator.object)
        {
          this.emitter.emit('entityChanged', this.modelManipulator.object);
        }
             if (mode !== 'view')
        {
          this.modelManipulator.attach(model);
          this.modelManipulator.mode = mode;
          this.modelManipulator.setMode( this.modelManipulator.mode );
          this.scene.add(this.modelManipulator.gizmo);
        }*/
      }
      /**
       * Toggle light visibility for the given entity. This will turn on/off
       * all lights that are children of the provided entity.
       * @param {string} Name of a THREE.Object3D.
       */

    }, {
      key: "toggleLights",
      value: function toggleLights(entityName) {
        // Turn off following if `entity` is null.
        if (entityName === undefined || entityName === null) {
          return;
        }
        /* Helper function to enable all child lights */


        function enableLightsHelper(obj) {
          if (obj === null || obj === undefined) {
            return;
          }

          if (obj.userData.hasOwnProperty("type") && obj.userData.type === "light") {
            obj.visible = !obj.visible;
          }
        } // Find the object and set the lights.


        var object = this.scene.getObjectByName(entityName);

        if (object !== null && object !== undefined) {
          object.traverse(enableLightsHelper);
        }
      }
      /**
       * Reset view
       */

    }, {
      key: "resetView",
      value: function resetView() {
        this.camera.position.copy(this.defaultCameraPosition);
        this.camera.up = new THREE__namespace.Vector3(0, 0, 1);
        this.camera.lookAt(this.defaultCameraLookAt);
        this.camera.updateMatrix();
      }
      /**
       * Take a screenshot of the canvas and save it.
       *
       * @param {string} filename - The filename of the screenshot. PNG extension is appended to it.
       */

    }, {
      key: "saveScreenshot",
      value: function saveScreenshot(filename) {
        // An explicit call to render is required. Otherwise the obtained image will be black.
        // See https://threejsfundamentals.org/threejs/lessons/threejs-tips.html, "Taking A Screenshot of the Canvas"
        this.render(0);
        this.getDomElement().toBlob(function (blob) {
          var url = URL.createObjectURL(blob);
          var linkElement = document.createElement("a");
          linkElement.href = url;
          linkElement.download = filename + ".png";
          document.body.appendChild(linkElement);
          linkElement.dispatchEvent(new MouseEvent("click"));
          document.body.removeChild(linkElement);
          URL.revokeObjectURL(url);
        });
      }
      /**
       * Generate thumbnails of the scene.
       *
       * The models on the scene should be previously scaled so that their maximum dimension equals 1.
       *
       * @param {string} filename - The filename of the generated zip file.
       * @param {THREE.Vector3} center - The point where the camera will point to.
       */

    }, {
      key: "createThumbnails",
      value: function createThumbnails(filename, center) {
        var _this5 = this;

        // Auxiliary method to return the canvas as a Promise.
        // This allows us to download all the images when they are ready.
        function getCanvasBlob(canvas) {
          return new Promise(function (resolve, reject) {
            canvas.toBlob(function (blob) {
              resolve(blob);
            });
          });
        }

        var zip = new JSZip__namespace();
        var canvas = this.getDomElement();
        var promises = []; // Directional light and target.

        var lightTarget = new THREE__namespace.Object3D();
        lightTarget.name = "thumbnails_light_target";
        lightTarget.position.copy(center);
        this.scene.add(lightTarget);
        var light = new THREE__namespace.DirectionalLight(0xffffff, 1.0);
        light.name = "thumbnails_light";
        this.scene.add(light);
        light.target = lightTarget; // Note: An explicit call to render is required for each image. Otherwise the obtained image will be black.
        // See https://threejsfundamentals.org/threejs/lessons/threejs-tips.html, "Taking A Screenshot of the Canvas"
        // Perspective

        this.camera.position.copy(center);
        this.camera.position.add(new THREE__namespace.Vector3(1.6, -1.6, 1.2));
        this.camera.lookAt(center);
        light.position.copy(this.camera.position);
        this.render(0);
        var perspective = getCanvasBlob(canvas);
        perspective.then(function (blob) {
          zip.file("thumbnails/1.png", blob);
        });
        promises.push(perspective); // Top

        this.camera.position.copy(center);
        this.camera.position.add(new THREE__namespace.Vector3(0, 0, 2.2));
        this.camera.rotation.copy(new THREE__namespace.Euler(0, 0, -90 * Math.PI / 180));
        light.position.copy(this.camera.position);
        this.render(0);
        var top = getCanvasBlob(canvas);
        top.then(function (blob) {
          zip.file("thumbnails/2.png", blob);
        });
        promises.push(top); // Front

        this.camera.position.copy(center);
        this.camera.position.add(new THREE__namespace.Vector3(2.2, 0, 0));
        this.camera.rotation.copy(new THREE__namespace.Euler(0, 90 * Math.PI / 180, 90 * Math.PI / 180));
        light.position.copy(this.camera.position);
        this.render(0);
        var front = getCanvasBlob(canvas);
        front.then(function (blob) {
          zip.file("thumbnails/3.png", blob);
        });
        promises.push(front); // Side

        this.camera.position.copy(center);
        this.camera.position.add(new THREE__namespace.Vector3(0, 2.2, 0));
        this.camera.rotation.copy(new THREE__namespace.Euler(-90 * Math.PI / 180, 0, 180 * Math.PI / 180));
        light.position.copy(this.camera.position);
        this.render(0);
        var side = getCanvasBlob(canvas);
        side.then(function (blob) {
          zip.file("thumbnails/4.png", blob);
        });
        promises.push(side); // Back

        this.camera.position.copy(center);
        this.camera.position.add(new THREE__namespace.Vector3(-2.2, 0, 0));
        this.camera.rotation.copy(new THREE__namespace.Euler(90 * Math.PI / 180, -90 * Math.PI / 180, 0));
        light.position.copy(this.camera.position);
        light.position.add(new THREE__namespace.Vector3(-2000, 0, 0));
        this.render(0);
        var back = getCanvasBlob(canvas);
        back.then(function (blob) {
          zip.file("thumbnails/5.png", blob);
        });
        promises.push(back);
        Promise.all(promises).then(function () {
          zip.generateAsync({
            type: "blob"
          }).then(function (content) {
            var url = URL.createObjectURL(content);
            var linkElement = document.createElement("a");
            linkElement.href = url;
            linkElement.download = filename + ".zip";
            document.body.appendChild(linkElement);
            linkElement.dispatchEvent(new MouseEvent("click"));
            document.body.removeChild(linkElement);
            URL.revokeObjectURL(url);
          });

          _this5.scene.remove(light);

          _this5.scene.remove(lightTarget);
        });
      }
      /**
       * Show radial menu
       * @param {} event
       */

    }, {
      key: "showRadialMenu",
      value: function showRadialMenu(e) {
        /*if (!this.radialMenu)
        {
          return;
        }
             var event = e.originalEvent;
             var pointer = event.touches ? event.touches[ 0 ] : event;
        var pos = new THREE.Vector2(pointer.clientX, pointer.clientY);
             var intersect = new THREE.Vector3();
        var model = this.getRayCastModel(pos, intersect);
             if (model && model.name !== '' && model.name !== 'plane'
            && this.modelManipulator.pickerNames.indexOf(model.name) === -1)
        {
          this.radialMenu.show(event,model);
          this.selectEntity(model);
        }*/
      }
      /**
       * Sets the bounding box of an object while ignoring the addtional visuals.
       * @param {THREE.Box3} - box
       * @param {THREE.Object3D} - object
       */

    }, {
      key: "setFromObject",
      value: function setFromObject(box, object) {
        box.min.x = box.min.y = box.min.z = +Infinity;
        box.max.x = box.max.y = box.max.z = -Infinity;
        var v = new THREE__namespace.Vector3();
        object.updateMatrixWorld(true);
        object.traverse(function (node) {
          var i, l;

          if (node instanceof THREE__namespace.Mesh) {
            var geometry = node.geometry;

            if (node.name !== "INERTIA_VISUAL" && node.name !== "COM_VISUAL") {
              if (geometry.isBufferGeometry) {
                var attribute = geometry.getAttribute("position");

                if (attribute !== undefined) {
                  for (i = 0, l = attribute.count; i < l; i++) {
                    v.fromBufferAttribute(attribute, i).applyMatrix4(node.matrixWorld);
                    expandByPoint(v);
                  }
                }
              } else {
                console.error("Unable to setFromObject");
              }
            }
          }
        });

        function expandByPoint(point) {
          box.min.min(point);
          box.max.max(point);
        }
      }
      /**
       * Show bounding box for a model. The box is aligned with the world.
       * @param {THREE.Object3D} model
       */

    }, {
      key: "showBoundingBox",
      value: function showBoundingBox(model) {
        if (typeof model === "string") {
          model = this.scene.getObjectByName(model);
        }

        if (this.boundingBox.visible) {
          if (this.boundingBox.parent === model) {
            return;
          } else {
            this.hideBoundingBox();
          }
        }

        var box = new THREE__namespace.Box3(); // w.r.t. world

        this.setFromObject(box, model); // center vertices with object

        box.min.x = box.min.x - model.position.x;
        box.min.y = box.min.y - model.position.y;
        box.min.z = box.min.z - model.position.z;
        box.max.x = box.max.x - model.position.x;
        box.max.y = box.max.y - model.position.y;
        box.max.z = box.max.z - model.position.z;
        var position = this.boundingBox.geometry.getAttribute("position"); //var array = position.array;

        position.setXYZ(0, box.max.x, box.max.y, box.max.z);
        position.setXYZ(1, box.min.x, box.max.y, box.max.z);
        position.setXYZ(2, box.min.x, box.min.y, box.max.z);
        position.setXYZ(3, box.max.x, box.min.y, box.max.z);
        position.setXYZ(4, box.max.x, box.max.y, box.min.z);
        position.setXYZ(5, box.min.x, box.max.y, box.min.z);
        position.setXYZ(6, box.min.x, box.min.y, box.min.z);
        position.setXYZ(7, box.max.x, box.min.y, box.min.z);
        position.needsUpdate = true;
        this.boundingBox.geometry.computeBoundingSphere(); // rotate the box back to the world

        var modelRotation = new THREE__namespace.Matrix4();
        modelRotation.extractRotation(model.matrixWorld);
        var modelInverse = new THREE__namespace.Matrix4();
        modelInverse.getInverse(modelRotation);
        this.boundingBox.quaternion.setFromRotationMatrix(modelInverse);
        this.boundingBox.name = "boundingBox";
        this.boundingBox.visible = true; // Add box as model's child

        model.add(this.boundingBox);
      }
      /**
       * Hide bounding box
       */

    }, {
      key: "hideBoundingBox",
      value: function hideBoundingBox() {
        if (this.boundingBox.parent) {
          this.boundingBox.parent.remove(this.boundingBox);
        }

        this.boundingBox.visible = false;
      }
      /**
       * Mouse right click
       * @param {} event
       * @param {} callback - function to be executed to the clicked model
       */

    }, {
      key: "onRightClick",
      value: function onRightClick(event, callback) {
        var pos = new THREE__namespace.Vector2(event.clientX, event.clientY);
        var model = this.getRayCastModel(pos, new THREE__namespace.Vector3());

        if (model && model.name !== "" && model.name !== "plane"
        /* &&
        this.modelManipulator.pickerNames.indexOf(model.name) === -1*/
        ) {
          callback(model);
        }
      }
      /**
       * Set model's view mode
       * @param {} model
       * @param {} viewAs (normal/transparent/wireframe)
       */

    }, {
      key: "setViewAs",
      value: function setViewAs(model, viewAs) {
        // Toggle
        if (model.userData.viewAs === viewAs) {
          viewAs = "normal";
        }

        var showWireframe = viewAs === "wireframe";

        function materialViewAs(material) {
          if (materials.indexOf(material.id) === -1) {
            materials.push(material.id);

            if (viewAs === "transparent") {
              if (material.opacity) {
                material.originalOpacity = material.opacity;
              } else {
                material.originalOpacity = 1.0;
              }

              material.opacity = 0.25;
              material.transparent = true;
            } else {
              material.opacity = material.originalOpacity ? material.originalOpacity : 1.0;

              if (material.opacity >= 1.0) {
                material.transparent = false;
              }
            } // wireframe handling


            material.wireframe = showWireframe;
          }
        }
        var descendants = [];
        var materials = [];
        getDescendants(model, descendants);

        for (var i = 0; i < descendants.length; ++i) {
          if (descendants[i].material && descendants[i].name.indexOf("boundingBox") === -1 && descendants[i].name.indexOf("COLLISION_VISUAL") === -1 && !this.getParentByPartialName(descendants[i], "COLLISION_VISUAL") && descendants[i].name.indexOf("wireframe") === -1 && descendants[i].name.indexOf("JOINT_VISUAL") === -1 && descendants[i].name.indexOf("COM_VISUAL") === -1 && descendants[i].name.indexOf("INERTIA_VISUAL") === -1) {
            if (Array.isArray(descendants[i].material)) {
              for (var k = 0; k < descendants[i].material.length; ++k) {
                materialViewAs(descendants[i].material[k]);
              }
            } else {
              materialViewAs(descendants[i].material);
            }
          }
        }

        if (!model.userData) {
          model.userData = new ModelUserData();
        }

        model.userData.viewAs = viewAs;
      }
      /**
       * Returns the closest parent whose name contains the given string
       * @param {} object
       * @param {} name
       */

    }, {
      key: "getParentByPartialName",
      value: function getParentByPartialName(object, name) {
        var parent = object.parent;

        while (parent && parent !== this.scene) {
          if (parent.name.indexOf(name) !== -1) {
            return parent;
          }

          parent = parent.parent;
        }

        return null;
      }
      /**
       * Select entity
       * @param {} object
       */

    }, {
      key: "selectEntity",
      value: function selectEntity(object) {
        if (object) {
          if (object !== this.selectedEntity) {
            this.showBoundingBox(object);
            this.selectedEntity = object;
          }

          this.attachManipulator(object, this.manipulationMode);
          this.emitter.emit("setTreeSelected", object.name);
        } else {
          /*if (this.modelManipulator.object)
          {
            this.modelManipulator.detach();
            this.scene.remove(this.modelManipulator.gizmo);
          }*/
          this.hideBoundingBox();
          this.selectedEntity = null;
          this.emitter.emit("setTreeDeselected");
        }
      }
      /**
       * View joints
       * Toggle: if there are joints, hide, otherwise, show.
       * @param {} model
       */

    }, {
      key: "viewJoints",
      value: function viewJoints(model) {
        if (model.joint === undefined || model.joint.length === 0) {
          return;
        }

        var child; // Visuals already exist

        if (model.jointVisuals) {
          // Hide = remove from parent
          if (model.jointVisuals[0].parent !== undefined && model.jointVisuals[0].parent !== null) {
            for (var v = 0; v < model.jointVisuals.length; ++v) {
              model.jointVisuals[v].parent.remove(model.jointVisuals[v]);
            }
          } // Show: attach to parent
          else {
            for (var s = 0; s < model.joint.length; ++s) {
              child = model.getObjectByName(model.joint[s].child);

              if (!child) {
                continue;
              }

              child.add(model.jointVisuals[s]);
            }
          }
        } // Create visuals
        else {
          model.jointVisuals = [];

          for (var j = 0; j < model.joint.length; ++j) {
            child = model.getObjectByName(model.joint[j].child);

            if (!child) {
              continue;
            } // XYZ expressed w.r.t. child


            var jointVisual = this.jointAxis["XYZaxes"].clone();
            child.add(jointVisual);
            model.jointVisuals.push(jointVisual);
            jointVisual.scale.set(0.7, 0.7, 0.7);
            this.setPose(jointVisual, model.joint[j].pose.position, model.joint[j].pose.orientation);
            var mainAxis = null;

            if (model.joint[j].type !== JointTypes.BALL && model.joint[j].type !== JointTypes.FIXED) {
              mainAxis = this.jointAxis["mainAxis"].clone();
              jointVisual.add(mainAxis);
            }

            var secondAxis = null;

            if (model.joint[j].type === JointTypes.REVOLUTE2 || model.joint[j].type === JointTypes.UNIVERSAL) {
              secondAxis = this.jointAxis["mainAxis"].clone();
              jointVisual.add(secondAxis);
            }

            if (model.joint[j].type === JointTypes.REVOLUTE || model.joint[j].type === JointTypes.GEARBOX) {
              mainAxis.add(this.jointAxis["rotAxis"].clone());
            } else if (model.joint[j].type === JointTypes.REVOLUTE2 || model.joint[j].type === JointTypes.UNIVERSAL) {
              mainAxis.add(this.jointAxis["rotAxis"].clone());
              secondAxis.add(this.jointAxis["rotAxis"].clone());
            } else if (model.joint[j].type === JointTypes.BALL) {
              jointVisual.add(this.jointAxis["ballVisual"].clone());
            } else if (model.joint[j].type === JointTypes.PRISMATIC) {
              mainAxis.add(this.jointAxis["transAxis"].clone());
            } else if (model.joint[j].type === JointTypes.SCREW) {
              mainAxis.add(this.jointAxis["screwAxis"].clone());
            }

            var direction, tempMatrix, rotMatrix;

            if (mainAxis) {
              // main axis expressed w.r.t. parent model or joint frame
              if (!model.joint[j].axis1) {
                console.error("no joint axis " + model.joint[j].type + "vs " + JointTypes.FIXED);
              }

              if (model.joint[j].axis1.use_parent_model_frame === undefined) {
                model.joint[j].axis1.use_parent_model_frame = true;
              }

              direction = new THREE__namespace.Vector3(model.joint[j].axis1.xyz.x, model.joint[j].axis1.xyz.y, model.joint[j].axis1.xyz.z);
              direction.normalize();
              tempMatrix = new THREE__namespace.Matrix4();

              if (model.joint[j].axis1.use_parent_model_frame) {
                tempMatrix.extractRotation(jointVisual.matrix);
                tempMatrix.getInverse(tempMatrix);
                direction.applyMatrix4(tempMatrix);
                tempMatrix.extractRotation(child.matrix);
                tempMatrix.getInverse(tempMatrix);
                direction.applyMatrix4(tempMatrix);
              }

              rotMatrix = new THREE__namespace.Matrix4();
              rotMatrix.lookAt(direction, new THREE__namespace.Vector3(0, 0, 0), mainAxis.up);
              mainAxis.quaternion.setFromRotationMatrix(rotMatrix);
            }

            if (secondAxis) {
              if (model.joint[j].axis2.use_parent_model_frame === undefined) {
                model.joint[j].axis2.use_parent_model_frame = true;
              }

              direction = new THREE__namespace.Vector3(model.joint[j].axis2.xyz.x, model.joint[j].axis2.xyz.y, model.joint[j].axis2.xyz.z);
              direction.normalize();
              tempMatrix = new THREE__namespace.Matrix4();

              if (model.joint[j].axis2.use_parent_model_frame) {
                tempMatrix.extractRotation(jointVisual.matrix);
                tempMatrix.getInverse(tempMatrix);
                direction.applyMatrix4(tempMatrix);
                tempMatrix.extractRotation(child.matrix);
                tempMatrix.getInverse(tempMatrix);
                direction.applyMatrix4(tempMatrix);
              }

              secondAxis.position = direction.multiplyScalar(0.3);
              rotMatrix = new THREE__namespace.Matrix4();
              rotMatrix.lookAt(direction, new THREE__namespace.Vector3(0, 0, 0), secondAxis.up);
              secondAxis.quaternion.setFromRotationMatrix(rotMatrix);
            }
          }
        }
      }
      /**
       * View Center Of Mass
       * Toggle: if there are COM visuals, hide, otherwise, show.
       * @param {} model
       */
      // This function needs to be migrated to ES6 and the latest THREE

      /*public viewCOM(model: any): void {
        if (model === undefined || model === null)
        {
          return;
        }
        if (model.children.length === 0)
        {
          return;
        }
           var child;
           // Visuals already exist
        if (model.COMVisuals)
        {
          // Hide = remove from parent
          if (model.COMVisuals[0].parent !== undefined &&
            model.COMVisuals[0].parent !== null)
          {
            for (var v = 0; v < model.COMVisuals.length; ++v)
            {
              for (var k = 0; k < 3; k++)
              {
                model.COMVisuals[v].parent.remove(model.COMVisuals[v].crossLines[k]);
              }
              model.COMVisuals[v].parent.remove(model.COMVisuals[v]);
            }
          }
          // Show: attach to parent
          else
          {
            for (var s = 0; s < model.children.length; ++s)
            {
              child = model.getObjectByName(model.children[s].name);
                 if (!child || child.name === 'boundingBox')
              {
                continue;
              }
                 child.add(model.COMVisuals[s].crossLines[0]);
              child.add(model.COMVisuals[s].crossLines[1]);
              child.add(model.COMVisuals[s].crossLines[2]);
              child.add(model.COMVisuals[s]);
            }
          }
        }
        // Create visuals
        else
        {
          model.COMVisuals = [];
          let COMVisual: THREE.Object3D;
          let helperGeometry_1: THREE.BufferGeometry;
          let helperGeometry_2: THREE.BufferGeometry;
          let helperGeometry_3: THREE.BufferGeometry;
             var box, line_1, line_2, line_3, helperMaterial, points = new Array(6);
          for (var j = 0; j < model.children.length; ++j)
          {
            child = model.getObjectByName(model.children[j].name);
               if (!child) {
              continue;
            }
               if (child.userData.inertial)
            {
              let inertialPose: Pose = new Pose();
              let userdatapose: Pose = new Pose();
              let inertialMass: number = 0;
              let radius: number = 0;
              var mesh = {};
              var inertial = child.userData.inertial;
                 userdatapose = child.userData.inertial.pose;
              inertialMass = inertial.mass;
                 // calculate the radius using lead density
              radius = Math.cbrt((0.75 * inertialMass ) / (Math.PI * 11340));
                 COMVisual = this.COMvisual.clone();
              child.add(COMVisual);
              model.COMVisuals.push(COMVisual);
              COMVisual.scale.set(radius, radius, radius);
                 var position = new THREE.Vector3(0, 0, 0);
                 // get euler rotation and convert it to Quaternion
              var quaternion = new THREE.Quaternion();
              var euler = new THREE.Euler(0, 0, 0, 'XYZ');
              quaternion.setFromEuler(euler);
                 inertialPose = {
                position: position,
                orientation: quaternion
              };
                 if (userdatapose !== undefined) {
                this.setPose(COMVisual, userdatapose.position,
                  userdatapose.orientation);
                  inertialPose = userdatapose;
              }
                 (COMVisual as any).crossLines = [];
                 // Store link's original rotation (w.r.t. the model)
              var originalRotation = new THREE.Euler();
              originalRotation.copy(child.rotation);
                 // Align link with world (reverse parent rotation w.r.t. the world)
              child.setRotationFromMatrix(
                new THREE.Matrix4().getInverse(child.parent.matrixWorld));
                 // Get its bounding box
              box = new THREE.Box3();
                 box.setFromObject(child);
                 // Rotate link back to its original rotation
              child.setRotationFromEuler(originalRotation);
                 // w.r.t child
              var worldToLocal = new THREE.Matrix4();
              worldToLocal.getInverse(child.matrixWorld);
              box.applyMatrix4(worldToLocal);
                 // X
              points[0] = new THREE.Vector3(box.min.x, inertialPose.position.y,
                inertialPose.position.z);
              points[1] = new THREE.Vector3(box.max.x, inertialPose.position.y,
                  inertialPose.position.z);
              // Y
              points[2] = new THREE.Vector3(inertialPose.position.x, box.min.y,
                    inertialPose.position.z);
              points[3] = new THREE.Vector3(inertialPose.position.x, box.max.y,
                      inertialPose.position.z);
              // Z
              points[4] = new THREE.Vector3(inertialPose.position.x,
                inertialPose.position.y, box.min.z);
              points[5] = new THREE.Vector3(inertialPose.position.x,
                inertialPose.position.y, box.max.z);
                 helperGeometry_1 = new THREE.BufferGeometry();
              helperGeometry_1.vertices.push(points[0]);
              helperGeometry_1.vertices.push(points[1]);
                 helperGeometry_2 = new THREE.BufferGeometry();
              helperGeometry_2.vertices.push(points[2]);
              helperGeometry_2.vertices.push(points[3]);
                 helperGeometry_3 = new THREE.Geometry();
              helperGeometry_3.vertices.push(points[4]);
              helperGeometry_3.vertices.push(points[5]);
                 helperMaterial = new THREE.LineBasicMaterial({color: 0x00ff00});
                 line_1 = new THREE.Line(helperGeometry_1, helperMaterial,
                  THREE.LineSegments);
              line_2 = new THREE.Line(helperGeometry_2, helperMaterial,
                  THREE.LineSegments);
              line_3 = new THREE.Line(helperGeometry_3, helperMaterial,
                  THREE.LineSegments);
                 line_1.name = 'COM_VISUAL';
              line_2.name = 'COM_VISUAL';
              line_3.name = 'COM_VISUAL';
              COMVisual.crossLines.push(line_1);
              COMVisual.crossLines.push(line_2);
              COMVisual.crossLines.push(line_3);
                 // show lines
              child.add(line_1);
              child.add(line_2);
              child.add(line_3);
             }
          }
        }
      }*/
      // TODO: Issue https://bitbucket.org/osrf/gzweb/issues/138

      /**
       * View inertia
       * Toggle: if there are inertia visuals, hide, otherwise, show.
       * @param {} model
       */
      // This function needs to be migrated to ES6 and the latest THREE

      /*public viewInertia(model: any): void {
        if (model === undefined || model === null)
        {
          return;
        }
           if (model.children.length === 0)
        {
          return;
        }
           var child;
           // Visuals already exist
        if (model.inertiaVisuals)
        {
          // Hide = remove from parent
          if (model.inertiaVisuals[0].parent !== undefined &&
            model.inertiaVisuals[0].parent !== null)
          {
            for (var v = 0; v < model.inertiaVisuals.length; ++v)
            {
              for (var k = 0; k < 3; k++)
              {
                model.inertiaVisuals[v].parent.remove(
                  model.inertiaVisuals[v].crossLines[k]);
              }
              model.inertiaVisuals[v].parent.remove(model.inertiaVisuals[v]);
            }
          }
          // Show: attach to parent
          else
          {
            for (var s = 0; s < model.children.length; ++s)
            {
              child = model.getObjectByName(model.children[s].name);
                 if (!child || child.name === 'boundingBox')
              {
                continue;
              }
              child.add(model.inertiaVisuals[s].crossLines[0]);
              child.add(model.inertiaVisuals[s].crossLines[1]);
              child.add(model.inertiaVisuals[s].crossLines[2]);
              child.add(model.inertiaVisuals[s]);
            }
          }
        }
        // Create visuals
        else
        {
          model.inertiaVisuals = [];
          var box , line_1, line_2, line_3, helperGeometry_1, helperGeometry_2,
          helperGeometry_3, helperMaterial, inertial, inertiabox,
          points = new Array(6);
          for (var j = 0; j < model.children.length; ++j)
          {
            child = model.getObjectByName(model.children[j].name);
               if (!child)
            {
              continue;
            }
               inertial = child.userData.inertial;
            if (inertial)
            {
              var mesh, boxScale, Ixx, Iyy, Izz, mass, inertia, material = {};
              let inertialPose: Pose;
                 if (inertial.pose)
              {
                inertialPose = child.userData.inertial.pose;
              }
              else if (child.position)
              {
                inertialPose.position = child.position;
                inertialPose.orientation = child.quaternion;
              }
              else
              {
                console.warn('Link pose not found!');
                continue;
              }
                 mass = inertial.mass;
              inertia = inertial.inertia;
              Ixx = inertia.ixx;
              Iyy = inertia.iyy;
              Izz = inertia.izz;
              boxScale = new THREE.Vector3();
                 if (mass < 0 || Ixx < 0 || Iyy < 0 || Izz < 0 ||
                Ixx + Iyy < Izz || Iyy + Izz < Ixx || Izz + Ixx < Iyy)
              {
                // Unrealistic inertia, load with default scale
                console.warn('The link ' + child.name + ' has unrealistic inertia, '
                      +'unable to visualize box of equivalent inertia.');
              }
              else
              {
                // Compute dimensions of box with uniform density
                // and equivalent inertia.
                boxScale.x = Math.sqrt(6*(Izz +  Iyy - Ixx) / mass);
                boxScale.y = Math.sqrt(6*(Izz +  Ixx - Iyy) / mass);
                boxScale.z = Math.sqrt(6*(Ixx  + Iyy - Izz) / mass);
                   inertiabox = new THREE.Object3D();
                inertiabox.name = 'INERTIA_VISUAL';
                   // Inertia indicator: equivalent box of uniform density
                mesh = this.createBox(1, 1, 1);
                mesh.name = 'INERTIA_VISUAL';
                material = {'ambient':[1,0.0,1,1],'diffuse':[1,0.0,1,1],
                  'depth_write':false,'opacity':0.5};
                this.setMaterial(mesh, material);
                inertiabox.add(mesh);
                inertiabox.name = 'INERTIA_VISUAL';
                child.add(inertiabox);
                   model.inertiaVisuals.push(inertiabox);
                inertiabox.scale.set(boxScale.x, boxScale.y, boxScale.z);
                inertiabox.crossLines = [];
                   this.setPose(inertiabox, inertialPose.position,
                  inertialPose.orientation);
                // show lines
                box = new THREE.Box3();
                // w.r.t. world
                box.setFromObject(child);
                points[0] = new THREE.Vector3(inertialPose.position.x,
                  inertialPose.position.y,
                  -2 * boxScale.z + inertialPose.position.z);
                points[1] = new THREE.Vector3(inertialPose.position.x,
                  inertialPose.position.y, 2 * boxScale.z + inertialPose.position.z);
                points[2] = new THREE.Vector3(inertialPose.position.x,
                  -2 * boxScale.y + inertialPose.position.y ,
                  inertialPose.position.z);
                points[3] = new THREE.Vector3(inertialPose.position.x,
                  2 * boxScale.y + inertialPose.position.y, inertialPose.position.z);
                points[4] = new THREE.Vector3(
                  -2 * boxScale.x + inertialPose.position.x,
                  inertialPose.position.y, inertialPose.position.z);
                points[5] = new THREE.Vector3(
                  2 * boxScale.x + inertialPose.position.x,
                  inertialPose.position.y, inertialPose.position.z);
                   helperGeometry_1 = new THREE.Geometry();
                helperGeometry_1.vertices.push(points[0]);
                helperGeometry_1.vertices.push(points[1]);
                   helperGeometry_2 = new THREE.Geometry();
                helperGeometry_2.vertices.push(points[2]);
                helperGeometry_2.vertices.push(points[3]);
                   helperGeometry_3 = new THREE.Geometry();
                helperGeometry_3.vertices.push(points[4]);
                helperGeometry_3.vertices.push(points[5]);
                   helperMaterial = new THREE.LineBasicMaterial({color: 0x00ff00});
                line_1 = new THREE.Line(helperGeometry_1, helperMaterial,
                    THREE.LineSegments);
                line_2 = new THREE.Line(helperGeometry_2, helperMaterial,
                  THREE.LineSegments);
                line_3 = new THREE.Line(helperGeometry_3, helperMaterial,
                  THREE.LineSegments);
                   line_1.name = 'INERTIA_VISUAL';
                line_2.name = 'INERTIA_VISUAL';
                line_3.name = 'INERTIA_VISUAL';
                inertiabox.crossLines.push(line_1);
                inertiabox.crossLines.push(line_2);
                inertiabox.crossLines.push(line_3);
                   // attach lines
                child.add(line_1);
                child.add(line_2);
                child.add(line_3);
              }
            }
          }
        }
      }*/

      /**
       * Update a light entity from a message
       * @param {} entity
       * @param {} msg
       */
      // This function needs to be migrated to ES6 and the latest THREE

      /*public updateLight(entity: any, msg: any): void {
        // TODO: Generalize this and createLight
        var lightObj = entity.children[0];
        var dir;
           var color = new THREE.Color();
           if (msg.diffuse)
        {
          color.r = msg.diffuse.r;
          color.g = msg.diffuse.g;
          color.b = msg.diffuse.b;
          lightObj.color = color.clone();
        }
        if (msg.specular)
        {
          color.r = msg.specular.r;
          color.g = msg.specular.g;
          color.b = msg.specular.b;
        }
           var matrixWorld;
        if (msg.pose)
        {
          // needed to update light's direction
          this.setPose(entity, msg.pose.position, msg.pose.orientation);
          entity.matrixWorldNeedsUpdate = true;
        }
           if (msg.range)
        {
          // THREE.js's light distance impacts the attenuation factor defined in the
          // shader:
          // attenuation factor = 1.0 - distance-to-enlighted-point / light.distance
          // Gazebo's range (taken from OGRE 3D API) does not contribute to
          // attenuation; it is a hard limit for light scope.
          // Nevertheless, we identify them for sake of simplicity.
          lightObj.distance = msg.range;
        }
           if (msg.cast_shadows)
        {
          lightObj.castShadow = msg.cast_shadows;
        }
           if (msg.attenuation_constant)
        {
          // no-op
        }
        if (msg.attenuation_linear)
        {
          lightObj.intensity = lightObj.intensity/(1+msg.attenuation_linear);
        }
        if (msg.attenuation_quadratic)
        {
          lightObj.intensity = lightObj.intensity/(1+msg.attenuation_quadratic);
        }
         //  Not handling these on gzweb for now
      //
      //  if (lightObj instanceof THREE.SpotLight) {
      //    if (msg.spot_outer_angle) {
      //      lightObj.angle = msg.spot_outer_angle;
      //    }
      //    if (msg.spot_falloff) {
      //      lightObj.exponent = msg.spot_falloff;
      //    }
      //  }
           if (msg.direction)
        {
          dir = new THREE.Vector3(msg.direction.x, msg.direction.y,
              msg.direction.z);
             entity.direction = new THREE.Vector3();
          entity.direction.copy(dir);
             if (lightObj.target)
          {
            lightObj.target.position.copy(dir);
          }
        }
      }*/

      /**
       * Adds an sdf model to the scene.
       * @param {object} sdf - It is either SDF XML string or SDF XML DOM object
       * @returns {THREE.Object3D}
       */
      // This function needs to be migrated to ES6 and the latest THREE

      /*public createFromSdf(sdf: any): THREE.Object3D {
        if (sdf === undefined)
        {
          console.error(' No argument provided ');
          return;
        }
           var obj = new THREE.Object3D();
           var sdfXml = this.spawnModel.sdfParser.parseXML(sdf);
        // sdfXML is always undefined, the XML parser doesn't work while testing
        // while it does work during normal usage.
        var myjson = xmlParser.xml2json(sdfXml, '\t');
        var sdfObj = JSON.parse(myjson).sdf;
           var mesh = this.spawnModel.sdfParser.spawnFromSDF(sdf);
        if (!mesh)
        {
          return;
        }
           obj.name = mesh.name;
        obj.add(mesh);
           return obj;
      }*/

      /**
       * Adds a lighting setup that is great for single model visualization. This
       * will not alter existing lights.
       */

    }, {
      key: "addModelLighting",
      value: function addModelLighting() {
        this.ambient.color = new THREE__namespace.Color(0x666666); // And light1. Upper back fill light.

        var light1 = this.createLight(3, // Diffuse
        new Color(0.2, 0.2, 0.2, 1.0), // Intensity
        0.5, // Pose
        new Pose(new THREE__namespace.Vector3(0, 10, 10), new THREE__namespace.Quaternion(0, 0, 0, 1)), // Distance
        undefined, // Cast shadows
        true, // Name
        "__model_light1__", // Direction
        new THREE__namespace.Vector3(0, -0.707, -0.707), // Specular
        new Color(0.3, 0.3, 0.3, 1.0));
        this.add(light1); // And light2. Lower back fill light

        var light2 = this.createLight(3, // Diffuse
        new Color(0.4, 0.4, 0.4, 1.0), // Intensity
        0.5, // Pose
        new Pose(new THREE__namespace.Vector3(0, 10, -10), new THREE__namespace.Quaternion(0, 0, 0, -1)), // Distance
        undefined, // Cast shadows
        true, // Name
        "__model_light2__", // Direction
        new THREE__namespace.Vector3(0, -0.707, 0.707), // Specular
        new Color(0.3, 0.3, 0.3, 1.0));
        this.add(light2); // And light3. Front fill light.

        var light3 = this.createLight(3, // Diffuse
        new Color(0.5, 0.5, 0.5, 1.0), // Intensity
        0.4, // Pose
        new Pose(new THREE__namespace.Vector3(-10, -10, 10), new THREE__namespace.Quaternion(0, 0, 0, 1)), // Distance
        undefined, // Cast shadows
        true, // Name
        "__model_light2__", // Direction
        new THREE__namespace.Vector3(0.707, 0.707, 0), // Specular
        new Color(0.3, 0.3, 0.3, 1.0));
        this.add(light3); // And light4. Front key light.

        var light4 = this.createLight(3, // Diffuse
        new Color(1, 1, 1, 1.0), // Intensity
        0.8, // Pose
        new Pose(new THREE__namespace.Vector3(10, -10, 10), new THREE__namespace.Quaternion(0, 0, 0, 1)), // Distance
        undefined, // Cast shadows
        true, // Name
        "__model_light2__", // Direction
        new THREE__namespace.Vector3(-0.707, 0.707, 0), // Specular
        new Color(0.8, 0.8, 0.8, 1.0));
        this.add(light4);
      }
      /**
       * Dispose all the resources used by the scene.
       *
       * This should be called whenever the visualization stops, in order to free resources.
       * See: https://threejs.org/docs/index.html#manual/en/introduction/How-to-dispose-of-objects
       */

    }, {
      key: "cleanup",
      value: function cleanup() {
        var objects = [];
        getDescendants(this.scene, objects);
        var that = this;
        objects.forEach(function (obj) {
          that.scene.remove(obj); // Dispose geometries.

          if (obj.geometry) {
            obj.geometry.dispose();
          } // Dispose materials and their textures.


          if (obj.material) {
            // Materials can be an array. If there is only one, convert it to an array for easier handling.
            if (!(obj.material instanceof Array)) {
              obj.material = [obj.material];
            } // Materials can have different texture maps, depending on their type.
            // We check each property of the Material and dispose them if they are Textures.


            obj.material.forEach(function (material) {
              Object.keys(material).forEach(function (property) {
                if (material[property] instanceof THREE__namespace.Texture) {
                  material[property].dispose();
                }
              });
              material.dispose();
            });
          }
        }); // Destroy particles.

        if (this.nebulaSystem) {
          this.nebulaSystem.destroy();
        } // Clean scene and renderer.


        this.renderer.renderLists.dispose();
        this.renderer.dispose();
      }
      /**
       * Set a request header for internal requests.
       *
       * @param {string} header - The header to send in the request.
       * @param {string} value - The value to set to the header.
       */

    }, {
      key: "setRequestHeader",
      value: function setRequestHeader(header, value) {
        // ES6 syntax for computed object keys.
        var headerObject = _defineProperty({}, header, value);

        this.textureLoader.requestHeader = headerObject;
        this.colladaLoader.requestHeader = headerObject;
        this.stlLoader.requestHeader = headerObject;
        this.requestHeader = headerObject; // Change the texture loader, if the requestHeader is present.
        // Texture Loaders use an Image Loader internally, instead of a File Loader.
        // Image Loader uses an img tag, and their src request doesn't accept
        // custom headers.
        // See https://github.com/mrdoob/three.js/issues/10439

        if (this.requestHeader) {
          this.textureLoader.load = function (url, onLoad, onProgress, onError) {
            var fileLoader = new THREE__namespace.FileLoader();
            fileLoader.setResponseType("blob");
            fileLoader.setRequestHeader(this.requestHeader);
            var texture = new THREE__namespace.Texture();
            var image = document.createElementNS("http://www.w3.org/1999/xhtml", "img"); // Once the image is loaded, we need to revoke the ObjectURL.

            image.onload = function () {
              image.onload = null;
              URL.revokeObjectURL(image.src);
              texture.image = image;
              texture.needsUpdate = true;

              if (onLoad) {
                onLoad(texture);
              }
            };

            image.onerror = onError; // Once the image is loaded, we need to revoke the ObjectURL.

            fileLoader.load(url, function (blob) {
              image.src = URL.createObjectURL(blob);
            }, onProgress, onError);
            return texture;
          };
        }
      }
      /**
       * Get the Nebula System.
       *
       * The System is usually required by render loops in order to be updated.
       *
       * @returns The Nebula System, or undefined if it wasn't set.
       */

    }, {
      key: "getParticleSystem",
      value: function getParticleSystem() {
        return this.nebulaSystem;
      }
      /**
       * Get the Nebula Renderer.
       *
       * Used by emitters to render particles.
       *
       * @returns The Nebula Renderer, or undefined if it wasn't set.
       */

    }, {
      key: "getParticleRenderer",
      value: function getParticleRenderer() {
        return this.nebulaRenderer;
      }
      /**
       * Set the Nebula System in order to use particles.
       *
       * @param system The Nebula System.
       * @param renderer The renderer the Nebula System will use.
       */

    }, {
      key: "setupParticleSystem",
      value: function setupParticleSystem(system, renderer) {
        this.nebulaSystem = system;
        this.nebulaRenderer = renderer;
      }
      /**
       * Print out the scene graph with position of each node.
       */

    }, {
      key: "printScene",
      value: function printScene() {
        var printGraph = function printGraph(obj) {
          console.group("<".concat(obj.type, "> ").concat(obj.name, " pos: ").concat(obj.position.x, ", ").concat(obj.position.y, ", ").concat(obj.position.z));
          obj.children.forEach(printGraph);
          console.groupEnd();
        };

        printGraph(this.scene);
      }
    }, {
      key: "loadTexture",
      value: function loadTexture(url, onLoad, onProgress) {
        var _this6 = this;

        // Return the cached texture if it exists.
        if (this.textureCache.has(url)) {
          return this.textureCache.get(url);
        }

        var fallbackLoader = function fallbackLoader(map, texture) {
          if (_this6.findResourceCb) {
            // Get the image using the find resource callback.
            _this6.findResourceCb(map, function (image, error) {
              if (error !== undefined) {
                // Mark the texture as error in the loading manager.
                var _manager5 = _this6.textureLoader.manager;

                _manager5.markAsError(map);

                return;
              } // Create the image element


              var imageElem = document.createElementNS("http://www.w3.org/1999/xhtml", "img");
              var isJPEG = map.search(/\.jpe?g($|\?)/i) > 0 || map.search(/^data\:image\/jpeg/) === 0;
              var binary = "";
              var len = image.byteLength;

              for (var i = 0; i < len; i++) {
                binary += String.fromCharCode(image[i]);
              } // Set the image source using base64 encoding


              imageElem.src = isJPEG ? "data:image/jpg;base64," : "data:image/png;base64,";
              imageElem.src += window.btoa(binary);
              texture.format = isJPEG ? THREE__namespace.RGBFormat : THREE__namespace.RGBAFormat;
              texture.needsUpdate = true;
              texture.image = imageElem; // Mark the texture as done in the loading manager.

              var manager = _this6.textureLoader.manager;
              manager.markAsDone(map);
            });
          }
        };

        var result = this.textureLoader.load(url, onLoad, onProgress, function (_error) {
          var scopeTexture = result;
          fallbackLoader(url, scopeTexture);
        }); // Cache the texture so that we don't try to load it multiple times.

        this.textureCache.set(url, result);
        return result;
      }
    }]);

    return Scene;
  }();

  var Shaders = /*#__PURE__*/_createClass(
  /**
   * @constructor
   * Holds custom shaders in string format which can be passed to
   * THREE.ShaderMaterial's options.
   */
  function Shaders() {
    _classCallCheck(this, Shaders);

    // Custom vertex shader for heightmaps
    this.heightmapVS = "varying vec2 vUv;" + "varying vec3 vPosition;" + "varying vec3 vNormal;" + "void main( void ) {" + "  vUv = uv;" + "  vPosition = position;" + "  vNormal = -normal;" + "  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);" + "}"; // Custom fragment shader for heightmaps

    this.heightmapFS = "uniform sampler2D texture0;" + "uniform sampler2D texture1;" + "uniform sampler2D texture2;" + "uniform float repeat0;" + "uniform float repeat1;" + "uniform float repeat2;" + "uniform float minHeight1;" + "uniform float minHeight2;" + "uniform float fadeDist1;" + "uniform float fadeDist2;" + "uniform vec3 ambient;" + "uniform vec3 lightDiffuse;" + "uniform vec3 lightDir;" + "varying vec2 vUv;" + "varying vec3 vPosition;" + "varying vec3 vNormal;" + "float blend(float distance, float fadeDist) {" + "  float alpha = distance / fadeDist;" + "  if (alpha < 0.0) {" + "    alpha = 0.0;" + "  }" + "  if (alpha > 1.0) {" + "    alpha = 1.0;" + "  }" + "  return alpha;" + "}" + "void main()" + "{" + "  vec3 diffuse0 = texture2D( texture0, vUv*repeat0 ).rgb;" + "  vec3 diffuse1 = texture2D( texture1, vUv*repeat1 ).rgb;" + "  vec3 diffuse2 = texture2D( texture2, vUv*repeat2 ).rgb;" + "  vec3 fragcolor = diffuse0;" + "  if (fadeDist1 > 0.0)" + "  {" + "    fragcolor = mix(" + "      fragcolor," + "      diffuse1," + "      blend(vPosition.z - minHeight1, fadeDist1)" + "    );" + "  }" + "  if (fadeDist2 > 0.0)" + "  {" + "    fragcolor = mix(" + "      fragcolor," + "      diffuse2," + "      blend(vPosition.z - (minHeight1 + minHeight2), fadeDist2)" + "    );" + "  }" + "  vec3 lightDirNorm = normalize(lightDir);" + "  float intensity = max(dot(vNormal, lightDirNorm), 0.0);" + "  vec3 vLightFactor = ambient + lightDiffuse * intensity;" + "  gl_FragColor = vec4(fragcolor.rgb * vLightFactor, 1.0);" + "}";
  });

  var Inertia = /*#__PURE__*/_createClass(function Inertia() {
    _classCallCheck(this, Inertia);
  });

  var Material = /*#__PURE__*/_createClass(function Material() {
    _classCallCheck(this, Material);

    this.texture = "";
    this.normalMap = "";
    this.opacity = 1.0;
    this.scale = 1.0;
  });

  var PBRMaterial = /*#__PURE__*/_createClass(function PBRMaterial() {
    _classCallCheck(this, PBRMaterial);

    this.albedoMap = "";
    this.normalMap = "";
    this.metalness = 0;
    this.metalnessMap = "";
    this.roughness = 0;
    this.roughnessMap = "";
    this.glossiness = 0;
    this.glossinessMap = "";
    this.specularMap = "";
    this.environmentMap = "";
    this.emissiveMap = "";
    this.lightMap = "";
    this.lightMapTexcoordSet = 0;
    this.ambientOcclusionMap = "";
  });

  var SDFParser = /*#__PURE__*/function () {
    /**
     * SDF parser constructor initializes SDF parser with the given parameters
     * and defines a DOM parser function to parse SDF XML files
     * @param {Scene} scene - the gz3d scene object
     **/
    function SDFParser(scene) {
      _classCallCheck(this, SDFParser);

      // true for using URLs to load files.
      // false for using the files loaded in the memory.
      this.usingFilesUrls = false; // Flag to control the usage of PBR materials (enabled by default).

      this.enablePBR = true;
      this.SDF_VERSION = 1.5;
      this.MATERIAL_ROOT = "assets";
      this.emitter = new eventemitter2.EventEmitter2({
        verboseMemoryLeak: true
      }); // cache materials if more than one model needs them

      this.materials = {};
      this.entityMaterial = {}; // store meshes when loading meshes from memory.

      this.meshes = {}; // Used to avoid loading meshes multiple times. An array that contains:
      // meshUri, submesh, material and the parent visual Object of the mesh.

      this.pendingMeshes = []; // This map is used to handle included models and avoid duplicated requests.
      // The key is the model's URI.
      // The value is an object that has a models array, which contains the pending models,
      // and it also contains the sdf, if it was read.
      // The value is an array of objects that contain the models that use the same uri and
      // their parents.
      // Models have a different name and pose that needs to be set once the model files resolve.
      // Map is not available in es5, so we need to suppress the linter warnings.

      this.pendingModels = new Map();
      this.mtls = {};
      this.textures = {}; // Should contain model files URLs if not using gzweb model files hierarchy.

      this.customUrls = [];
      this.scene = scene;
      this.scene.setSDFParser(this);
      this.scene.initScene();
      var that = this;
      this.emitter.on("material", function (mat) {
        that.materials = Object.assign(that.materials, mat);
      });
      this.fuelServer = new FuelServer();
    }
    /**
     * Pushes Urls into the customUrls array where the parser looks for assets.
     * If `usingFilesUrls` is true, resources will only be taken from this array.
     * TODO: Find a less intrusive way to support custom URLs (issue #147)
     */


    _createClass(SDFParser, [{
      key: "addUrl",
      value: function addUrl(url) {
        var trimmedUrl = url && url.trim();

        if (trimmedUrl === undefined || trimmedUrl.indexOf("http") !== 0) {
          console.warn("Trying to add invalid URL: " + url);
          return;
        } // Avoid duplicated URLs.


        if (this.customUrls.indexOf(trimmedUrl) === -1) {
          this.customUrls.push(trimmedUrl);
        }
      }
      /**
       * Parses a color, which may come from an object or string.
       * @param {string|object} colorInput - A string which denotes the color where every value
       * should be separated with single white space, or an object containing rgba values
       * @returns {object} color - color object having r, g, b and alpha values
       */

    }, {
      key: "parseColor",
      value: function parseColor(colorInput) {
        var color = new Color();
        var values = [];

        if (typeof colorInput === "string") {
          values = colorInput.split(/\s+/);
        } else {
          values = [colorInput["r"] || 0, colorInput["g"] || 0, colorInput["b"] || 0, colorInput["a"] || 1];
        }

        color.r = parseFloat(values[0]);
        color.g = parseFloat(values[1]);
        color.b = parseFloat(values[2]);
        color.a = parseFloat(values[3]);
        return color;
      }
      /**
       * Parses string which is a 3D vector
       * @param {string|object} vectorInput - string which denotes the vector where every value
       * should be separated with single white space, or an object containing x, y, z values.
       * @returns {object} vector3D - vector having x, y, z values
       */

    }, {
      key: "parse3DVector",
      value: function parse3DVector(vectorInput) {
        var vector3D = new THREE__namespace.Vector3();
        var values = [];

        if (typeof vectorInput === "string") {
          values = vectorInput.split(/\s+/);
        } else {
          values = [vectorInput["x"] || 0, vectorInput["y"] || 0, vectorInput["z"] || 0];
        }

        vector3D.x = parseFloat(values[0]);
        vector3D.y = parseFloat(values[1]);
        vector3D.z = parseFloat(values[2]);
        return new THREE__namespace.Vector3(vector3D.x, vector3D.y, vector3D.z);
      }
      /**
       * Creates a light from either a protobuf object or SDF object.
       * @param {object} light - A light represented by a Protobuf or SDF object.
       * @returns {THREE.Light} lightObj - THREE light object created
       * according to given properties. The type of light object is determined
       * according to light type
       */

    }, {
      key: "spawnLight",
      value: function spawnLight(light) {
        if (light.type !== undefined && !(light.type instanceof String)) {
          return this.spawnLightFromProto(light);
        } else {
          return this.spawnLightFromSDF({
            light: light
          });
        }
      }
      /**
       * Creates THREE light object according to properties of sdf object
       * which is parsed from sdf model of the light
       * @param {object} sdfObj - object which is parsed from the sdf string
       * @returns {THREE.Object3D} lightObj - THREE.Object3D that holds the
       * THREE.Light created according to given properties. The type of light
       * object is determined according to light type
       */

    }, {
      key: "spawnLightFromSDF",
      value: function spawnLightFromSDF(sdfObj) {
        var light = sdfObj.light;
        var name = light["@name"] || light["name"];
        var diffuse = this.parseColor(light.diffuse);
        var specular = this.parseColor(light.specular);
        var pose = this.parsePose(light.pose);
        var castShadows = this.parseBool(light.cast_shadows);
        var distance = 0.0;
        var attConst = 0.0;
        var attLin = 0.0;
        var attQuad = 0.0;
        var direction;
        var innerAngle = 0.0;
        var outerAngle = 0.0;
        var falloff = 0.0;
        var type = 1;

        if (light.attenuation) {
          if (light.attenuation.range) {
            distance = parseFloat(light.attenuation.range);
          }

          if (light.attenuation.constant) {
            attConst = parseFloat(light.attenuation.constant);
          }

          if (light.attenuation.linear) {
            attLin = parseFloat(light.attenuation.linear);
          }

          if (light.attenuation.quadratic) {
            attQuad = parseFloat(light.attenuation.quadratic);
          }
        }

        if (light.spot) {
          if (light.spot.inner_angle) {
            innerAngle = parseFloat(light.spot.inner_angle);
          }

          if (light.spot.outer_angle) {
            outerAngle = parseFloat(light.spot.outer_angle);
          }

          if (light.spot.falloff) {
            falloff = parseFloat(light.spot.falloff);
          }
        } // equation taken from
        // eslint-disable-next-line
        // https://docs.blender.org/manual/en/dev/render/blender_render/lighting/lights/light_attenuation.html


        var E = 1;
        var D = 1;
        var r = 1;
        var L = attLin;
        var Q = attQuad;
        var intensity = E * (D / (D + L * r)) * (Math.pow(D, 2) / (Math.pow(D, 2) + Q * Math.pow(r, 2)));

        if (light["@type"] === "point") {
          type = 1;
        }

        if (light["@type"] === "spot") {
          type = 2;
        } else if (light["@type"] === "directional") {
          type = 3;
          direction = this.parse3DVector(light.direction);
        }

        var lightObj = this.scene.createLight(type, diffuse, intensity, pose, distance, castShadows, name, direction, specular, attConst, attLin, attQuad, innerAngle, outerAngle, falloff);
        return lightObj;
      }
      /**
       * Creates THREE light object according to properties of protobuf object
       * @param {object} pbObj - object which is parsed from a Protobuf string
       * @returns {THREE.Light} lightObj - THREE.Object3d that holds the
       * THREE.Light object created according to given properties. The type of
       * light object is determined according to light type
       */

    }, {
      key: "spawnLightFromProto",
      value: function spawnLightFromProto(light) {
        // equation taken from
        // eslint-disable-next-line
        // https://docs.blender.org/manual/en/dev/render/blender_render/lighting/lights/light_attenuation.html
        var E = 1;
        var D = 1;
        var r = 1;
        var L = light.attenuation_linear;
        var Q = light.attenuation_quadratic;
        var intensity = E * (D / (D + L * r)) * (Math.pow(D, 2) / (Math.pow(D, 2) + Q * Math.pow(r, 2)));
        var lightObj = this.scene.createLight( // Protobuf light type starts at zero.
        light.type + 1, light.diffuse, intensity, light.pose, light.range, light.cast_shadows, light.name, light.direction, light.specular, light.attenuation_constant, light.attenuation_linear, light.attenuation_quadratic, light.spot_inner_angle, light.spot_outer_angle, light.spot_falloff);
        return lightObj;
      }
      /**
       * Parses a string which is a 3D vector
       * @param {string|object} poseInput - string which denotes the pose of the object
       * where every value should be separated with single white space and
       * first three denotes x,y,z and values of the pose,
       * and following three denotes euler rotation around x,y,z, or an object
       * containing pose and orientation.
       * @returns {object} pose - pose object having position (x,y,z)(THREE.Vector3)
       * and orientation (THREE.Quaternion) properties
       */

    }, {
      key: "parsePose",
      value: function parsePose(poseInput) {
        var pose = new Pose(); // Short circuit if poseInput is undefined

        if (poseInput === undefined) {
          return pose;
        }

        if (poseInput.hasOwnProperty("position") && poseInput.hasOwnProperty("orientation")) {
          pose.position.x = poseInput["position"]["x"];
          pose.position.y = poseInput["position"]["y"];
          pose.position.z = poseInput["position"]["z"];
          pose.orientation.x = poseInput["orientation"]["x"];
          pose.orientation.y = poseInput["orientation"]["y"];
          pose.orientation.z = poseInput["orientation"]["z"];
          pose.orientation.w = poseInput["orientation"]["w"];
          return pose;
        }

        var poseStr = "";

        if (_typeof(poseInput) === "object") {
          // Note: The pose might have an empty frame attribute. This is a valid XML
          // element though. In this case, the parser outputs
          // {@frame: "frame", #text: "pose value"}
          if (poseInput.hasOwnProperty("@frame")) {
            console.warn("SDFParser does not support frame semantics.");
          }

          poseStr = poseInput["#text"];
        } else {
          poseStr = poseInput;
        }

        var values = poseStr.trim().split(/\s+/);
        pose.position.x = parseFloat(values[0]);
        pose.position.y = parseFloat(values[1]);
        pose.position.z = parseFloat(values[2]); // get euler rotation and convert it to Quaternion

        var euler = new THREE__namespace.Euler(parseFloat(values[3]), parseFloat(values[4]), parseFloat(values[5]), "ZYX");
        pose.orientation.setFromEuler(euler);
        return pose;
      }
      /**
       * Parses a string which is a 3D vector
       * @param {string|object} scaleInput - string which denotes scaling in x,y,z
       * where every value should be separated with single white space, or an object
       * containing x, y, z values.
       * @returns {THREE.Vector3} scale - THREE Vector3 object
       * which denotes scaling of an object in x,y,z
       */

    }, {
      key: "parseScale",
      value: function parseScale(scaleInput) {
        var values = [];

        if (typeof scaleInput === "string") {
          values = scaleInput.split(/\s+/);
        } else {
          values = [scaleInput["x"] || 1, scaleInput["y"] || 1, scaleInput["z"] || 1];
        }

        var scale = new THREE__namespace.Vector3(parseFloat(values[0]), parseFloat(values[1]), parseFloat(values[2]));
        return scale;
      }
      /**
       * Parses a string which is a boolean
       * @param {string} boolStr - string which denotes a boolean value
       * where the values can be true, false, 1, or 0.
       * @returns {bool} bool - bool value
       */

    }, {
      key: "parseBool",
      value: function parseBool(boolStr) {
        if (boolStr !== undefined) {
          return JSON.parse(boolStr);
        }

        return false;
      }
      /**
       * Parses SDF material element which is going to be used by THREE library
       * It matches material scripts with the material objects which are
       * already parsed by gzbridge and saved by SDFParser.
       * If `usingFilesUrls` is true, the texture URLs will be loaded from the
       * to the customUrls array.
       * @param {object} material - SDF or Protobuf material object
       * @returns {object} material - material object which has the followings:
       * texture, normalMap, ambient, diffuse, specular, opacity
       */

    }, {
      key: "createMaterial",
      value: function createMaterial(srcMaterial) {
        var material = new Material();

        if (!srcMaterial) {
          return undefined;
        }

        if (srcMaterial.ambient) {
          material.ambient = this.parseColor(srcMaterial.ambient);
        }

        if (srcMaterial.diffuse) {
          material.diffuse = this.parseColor(srcMaterial.diffuse);
        }

        if (srcMaterial.specular) {
          material.specular = this.parseColor(srcMaterial.specular);
        }

        material.opacity = srcMaterial.opacity;
        material.normalMap = srcMaterial.normalMap;
        material.scale = srcMaterial.scale; // normal map

        if (srcMaterial.normal_map) {
          var mapUri = "";

          if (srcMaterial.normal_map.indexOf("://") > 0) {
            mapUri = srcMaterial.normal_map.substring(srcMaterial.normal_map.indexOf("://") + 3, srcMaterial.normal_map.lastIndexOf("/"));
          }

          if (mapUri != "") {
            var startIndex = srcMaterial.normal_map.lastIndexOf("/") + 1;

            if (startIndex < 0) {
              startIndex = 0;
            }

            var normalMapName = srcMaterial.normal_map.substr(startIndex, srcMaterial.normal_map.lastIndexOf(".") - startIndex); // Map texture name to the corresponding texture.

            if (!this.usingFilesUrls) {
              material.normalMap = this.textures[normalMapName + ".png"];
            } else {
              if (this.customUrls.length !== 0) {
                for (var j = 0; j < this.customUrls.length; j++) {
                  if (this.customUrls[j].indexOf(normalMapName + ".png") > -1) {
                    material.normalMap = this.customUrls[j];
                    break;
                  }
                }
              } else {
                material.normalMap = this.MATERIAL_ROOT + "/" + mapUri + "/" + normalMapName + ".png";
              }
            }
          }
        } // Material properties received via a protobuf message are formatted
        // differently from SDF. This will map protobuf format onto sdf.


        if (srcMaterial.pbr && this.enablePBR) {
          material.pbr = new PBRMaterial();

          if (srcMaterial.pbr.metal) {
            // Must be SDF with metal properties.
            material.pbr.albedoMap = srcMaterial.pbr.metal.albedo_map;
            material.pbr.metalness = srcMaterial.pbr.metal.metalness;
            material.pbr.metalnessMap = srcMaterial.pbr.metal.metalness_map;
            material.pbr.normalMap = srcMaterial.pbr.metal.normal_map;
            material.pbr.roughness = srcMaterial.pbr.metal.roughness;
            material.pbr.roughnessMap = srcMaterial.pbr.metal.roughness_map;
            material.pbr.emissiveMap = srcMaterial.pbr.metal.emissive_map;
            material.pbr.lightMap = srcMaterial.pbr.metal.light_map;
            material.pbr.environmentMap = srcMaterial.pbr.metal.environment_map;
            material.pbr.ambientOcclusionMap = srcMaterial.pbr.metal.ambient_occlusion_map;
          } else if (srcMaterial.pbr.specular) {
            // Must be SDF with specular properties.
            material.pbr.albedoMap = srcMaterial.pbr.specular.albedo_map;
            material.pbr.specularMap = srcMaterial.pbr.specular.specular_map;
            material.pbr.glossinessMap = srcMaterial.pbr.specular.glossiness_map;
            material.pbr.glossiness = srcMaterial.pbr.specular.glossiness;
            material.pbr.environmentMap = srcMaterial.pbr.specular.environment_map;
            material.pbr.ambientOcclusionMap = srcMaterial.pbr.specular.ambient_occlusion_map;
            material.pbr.normalMap = srcMaterial.pbr.specular.normal_map;
            material.pbr.emissiveMap = srcMaterial.pbr.specular.emissive_map;
            material.pbr.lightMap = srcMaterial.pbr.specular.light_map;
          } else {
            // Must be a protobuf message.
            material.pbr.albedoMap = srcMaterial.pbr.albedo_map;
            material.pbr.normalMap = srcMaterial.pbr.normal_map;
            material.pbr.metalness = srcMaterial.pbr.metalness;
            material.pbr.metalnessMap = srcMaterial.pbr.metalness_map;
            material.pbr.roughness = srcMaterial.pbr.roughness;
            material.pbr.roughnessMap = srcMaterial.pbr.roughness_map;
            material.pbr.glossiness = srcMaterial.pbr.glossiness;
            material.pbr.glossinessMap = srcMaterial.pbr.glossiness_map;
            material.pbr.specularMap = srcMaterial.pbr.specular_map;
            material.pbr.environmentMap = srcMaterial.pbr.environment_map;
            material.pbr.emissiveMap = srcMaterial.pbr.emissive_map;
            material.pbr.lightMap = srcMaterial.pbr.light_map;
            material.pbr.ambientOcclusionMap = srcMaterial.pbr.ambient_occlusion_map;
          }
        } // Set the correct URLs of the PBR-related textures, if available.


        if (material.pbr && this.enablePBR) {
          // Iterator for the subsequent for loops. Used to avoid a linter warning.
          // Loops (and all variables in general) should use let/const when ported to ES6.
          var u;

          if (material.pbr.albedoMap) {
            var albedoMap = "";
            var albedoMapName = material.pbr.albedoMap.split("/").pop();

            if (material.pbr.albedoMap.startsWith("https://")) {
              this.addUrl(material.pbr.albedoMap);
            }

            if (this.usingFilesUrls && this.customUrls.length !== 0) {
              for (var _u = 0; _u < this.customUrls.length; _u++) {
                if (this.customUrls[_u].indexOf(albedoMapName) > -1) {
                  albedoMap = this.customUrls[_u];
                  break;
                }
              }

              if (albedoMap) {
                material.pbr.albedoMap = albedoMap;
              } else {
                console.error("Missing Albedo Map file [" + material.pbr.albedoMap + "]"); // Prevent the map from loading, as it hasn't been found.

                material.pbr.albedoMap = "";
              }
            }
          }

          if (material.pbr.emissiveMap) {
            var emissiveMap = "";
            var emissiveMapName = material.pbr.emissiveMap.split("/").pop();

            if (material.pbr.emissiveMap.startsWith("https://")) {
              this.addUrl(material.pbr.emissiveMap);
            }

            if (this.usingFilesUrls && this.customUrls.length !== 0) {
              for (u = 0; u < this.customUrls.length; u++) {
                if (this.customUrls[u].indexOf(emissiveMapName) > -1) {
                  emissiveMap = this.customUrls[u];
                  break;
                }
              }

              if (emissiveMap) {
                material.pbr.emissiveMap = emissiveMap;
              } else {
                console.error("Missing Emissive Map file [" + material.pbr.emissiveMap + "]"); // Prevent the map from loading, as it hasn't been found.

                material.pbr.emissiveMap = "";
              }
            }
          }

          if (material.pbr.normalMap) {
            var pbrNormalMap = "";
            var pbrNormalMapName = material.pbr.normalMap.split("/").pop();

            if (material.pbr.normalMap.startsWith("https://")) {
              this.addUrl(material.pbr.normalMap);
            }

            if (this.usingFilesUrls && this.customUrls.length !== 0) {
              for (u = 0; u < this.customUrls.length; u++) {
                if (this.customUrls[u].indexOf(pbrNormalMapName) > -1) {
                  pbrNormalMap = this.customUrls[u];
                  break;
                }
              }

              if (pbrNormalMap) {
                material.pbr.normalMap = pbrNormalMap;
              } else {
                console.error("Missing Normal Map file [" + material.pbr.normalMap + "]"); // Prevent the map from loading, as it hasn't been found.

                material.pbr.normalMap = "";
              }
            }
          }

          if (material.pbr.roughnessMap) {
            var roughnessMap = "";
            var roughnessMapName = material.pbr.roughnessMap.split("/").pop();

            if (material.pbr.roughnessMap.startsWith("https://")) {
              this.addUrl(material.pbr.roughnessMap);
            }

            if (this.usingFilesUrls && this.customUrls.length !== 0) {
              for (u = 0; u < this.customUrls.length; u++) {
                if (this.customUrls[u].indexOf(roughnessMapName) > -1) {
                  roughnessMap = this.customUrls[u];
                  break;
                }
              }

              if (roughnessMap) {
                material.pbr.roughnessMap = roughnessMap;
              } else {
                console.error("Missing Roughness Map file [" + material.pbr.roughnessMap + "]"); // Prevent the map from loading, as it hasn't been found.

                material.pbr.roughnessMap = "";
              }
            }
          }

          if (material.pbr.metalnessMap) {
            var metalnessMap = "";
            var metalnessMapName = material.pbr.metalnessMap.split("/").pop();

            if (material.pbr.metalnessMap.startsWith("https://")) {
              this.addUrl(material.pbr.metalnessMap);
            }

            if (this.usingFilesUrls && this.customUrls.length !== 0) {
              for (u = 0; u < this.customUrls.length; u++) {
                if (this.customUrls[u].indexOf(metalnessMapName) > -1) {
                  metalnessMap = this.customUrls[u];
                  break;
                }
              }

              if (metalnessMap) {
                material.pbr.metalnessMap = metalnessMap;
              } else {
                console.error("Missing Metalness Map file [" + material.pbr.metalnessMap + "]"); // Prevent the map from loading, as it hasn't been found.

                material.pbr.metalnessMap = "";
              }
            }
          }
        }

        return material;
      }
      /**
       * Parses a string which is a size of an object
       * @param {string|object} sizeInput - string which denotes size in x,y,z
       * where every value should be separated with single white space, or an object
       * containing x, y, z values.
       * @returns {object} size - size object which denotes
       * size of an object in x,y,z
       */

    }, {
      key: "parseSize",
      value: function parseSize(sizeInput) {
        if (typeof sizeInput === "string") {
          var values = sizeInput.split(/\s+/);
          return new THREE__namespace.Vector3(parseFloat(values[0]), parseFloat(values[1]), parseFloat(values[2]));
        }

        return new THREE__namespace.Vector3(sizeInput.x, sizeInput.y, sizeInput.z);
      }
      /**
       * Parses SDF geometry element and creates corresponding mesh,
       * when it creates the THREE.Mesh object it directly add it to the parent
       * object.
       * @param {object} geom - SDF geometry object which determines the geometry
       *  of the object and can have following properties: box, cylinder, sphere,
       *  plane, mesh, capsule.
       *  Note that in case of using custom URLs for the meshes, the URLs should be
       *  added to the array customUrls to be used instead of the default URL.
       * @param {object} mat - SDF material object which is going to be parsed
       * by createMaterial function
       * @param {object} parent - parent 3D object
       * @param {object} options - Options to send to the creation process. It can include:
       *                 - enableLights - True to have lights visible when the object is created.
       *                                  False to create the lights, but set them to invisible (off).
       *                 - fuelName - Name of the resource in Fuel. Helps to match URLs to the correct path. Requires 'fuelOwner'.
       *                 - fuelOwner - Name of the resource's owner in Fuel. Helps to match URLs to the correct path. Requires 'fuelName'.
       */

    }, {
      key: "createGeom",
      value: function createGeom(geom, mat, parent, options) {
        var that = this;
        var obj = undefined;
        var size;
        var normal = new THREE__namespace.Vector3(0, 0, 1);
        var material = this.createMaterial(mat);

        if (geom.box) {
          if (geom.box.size) {
            size = this.parseSize(geom.box.size);
          } else {
            size = {
              x: 1,
              y: 1,
              z: 1
            };
          }

          obj = this.scene.createBox(size.x, size.y, size.z);
        } else if (geom.cylinder) {
          var radius = parseFloat(geom.cylinder.radius);
          var length = parseFloat(geom.cylinder.length);
          obj = this.scene.createCylinder(radius, length);
        } else if (geom.capsule) {
          var radius = parseFloat(geom.capsule.radius);
          var length = parseFloat(geom.capsule.length);
          obj = this.scene.createCapsule(radius, length);
        } else if (geom.cone) {
          var radius = parseFloat(geom.cone.radius);
          var length = parseFloat(geom.cone.length);
          obj = this.scene.createCone(radius, length);
        } else if (geom.ellipsoid) {
          var radii = this.parseSize(geom.ellipsoid.radii);
          obj = this.scene.createEllipsoid(radii.x, radii.y, radii.z);
        } else if (geom.sphere) {
          obj = this.scene.createSphere(parseFloat(geom.sphere.radius));
        } else if (geom.plane) {
          if (geom.plane.normal) {
            normal = this.parseSize(geom.plane.normal);
          }

          if (geom.plane.size) {
            size = this.parseSize(geom.plane.size);
          } else {
            size = {
              x: 1,
              y: 1
            };
          }

          obj = this.scene.createPlane(normal, size.x, size.y);
        } else if (geom.mesh) {
          var meshUri = geom.mesh.uri || geom.mesh.filename;
          var submesh = "";
          var centerSubmesh = false;
          var modelName = "";

          if (geom.mesh.submesh) {
            // Submesh information coming from protobuf messages is slightly
            // different than submesh information coming from an SDF file.
            //
            // * protobuf message has 'submesh' and 'center_submesh'
            // * SDF file has 'submesh.name' and 'submesh.center'
            if (geom.mesh.center_submesh !== undefined) {
              submesh = geom.mesh.submesh;
              centerSubmesh = this.parseBool(geom.mesh.center_submesh);
            } else {
              submesh = geom.mesh.submesh.name;
              centerSubmesh = this.parseBool(geom.mesh.submesh.center);
            }
          }

          var uriType = meshUri.substring(0, meshUri.indexOf("://"));

          if (uriType === "file" || uriType === "model") {
            modelName = meshUri.substring(meshUri.indexOf("://") + 3);
          } else {
            modelName = meshUri;
          }

          if (geom.mesh.scale) {
            var scale = this.parseScale(geom.mesh.scale);
            parent.scale.x = scale.x;
            parent.scale.y = scale.y;
            parent.scale.z = scale.z;
          } // Create a valid Fuel URI from the model name


          var modelUri = createFuelUri(modelName);
          var ext = modelUri.substr(-4).toLowerCase();
          var materialName = parent.name + "::" + modelUri;
          this.entityMaterial[materialName] = material;
          var meshFileName = meshUri.substring(meshUri.lastIndexOf("/"));

          if (!this.usingFilesUrls) {
            var meshFile = this.meshes[meshFileName];

            if (!meshFile) {
              console.error("Missing mesh file [" + meshFileName + "]");
              return;
            }

            if (ext === ".obj") {
              var mtlFileName = meshFileName.split(".")[0] + ".mtl";
              var mtlFile = this.mtls[mtlFileName];

              if (!mtlFile) {
                console.error("Missing MTL file [" + mtlFileName + "]");
                return;
              }

              that.scene.loadMeshFromString(modelUri, submesh, centerSubmesh, function (obj) {
                if (!obj) {
                  console.error("Failed to load mesh.");
                  return;
                }

                parent.add(obj);
                loadGeom(parent);
              }, // onError callback
              function (error) {
                console.error(error);
              }, [meshFile, mtlFile]);
            } else if (ext === ".dae") {
              that.scene.loadMeshFromString(modelUri, submesh, centerSubmesh, function (dae) {
                if (!dae) {
                  console.error("Failed to load mesh.");
                  return;
                }

                if (material) {
                  var allChildren = [];
                  getDescendants(dae, allChildren);

                  for (var c = 0; c < allChildren.length; ++c) {
                    if (allChildren[c] instanceof THREE__namespace.Mesh) {
                      that.scene.setMaterial(allChildren[c], material);
                      break;
                    }
                  }
                }

                parent.add(dae);
                loadGeom(parent);
              }, // onError callback
              function (error) {
                console.error(error);
              }, [meshFile]);
            }
          } else {
            if (this.customUrls.length !== 0) {
              for (var k = 0; k < this.customUrls.length; k++) {
                if (this.customUrls[k].indexOf(meshFileName) > -1) {
                  // If we have Fuel name and owner information, make sure the
                  // path includes them.
                  if (options && options.fuelName && options.fuelOwner) {
                    if (this.customUrls[k].indexOf(options.fuelName) > -1 && this.customUrls[k].indexOf(options.fuelOwner) > -1) {
                      modelUri = this.customUrls[k];
                      break;
                    }
                  } else {
                    // No Fuel name and owner provided. Use the filename.
                    modelUri = this.customUrls[k];
                    break;
                  }
                }
              }
            } // Avoid loading the mesh multiple times.


            for (var i = 0; i < this.pendingMeshes.length; i++) {
              if (this.pendingMeshes[i].meshUri === modelUri) {
                // The mesh is already pending, but submesh and the visual object
                // parent are different.
                this.pendingMeshes.push({
                  meshUri: modelUri,
                  submesh: submesh,
                  parent: parent,
                  material: material,
                  centerSubmesh: centerSubmesh
                }); // If the mesh exists, then create another version and add it to
                // the parent object.

                if (this.scene.meshes.has(modelUri)) {
                  var mesh = this.scene.meshes.get(modelUri);

                  if (parent.getObjectByName(mesh.name) === undefined) {
                    mesh = mesh.clone();
                    this.scene.useSubMesh(mesh, submesh, centerSubmesh);
                    parent.add(mesh);
                    loadGeom(parent);
                  }
                }

                return;
              }
            }

            this.pendingMeshes.push({
              meshUri: modelUri,
              submesh: submesh,
              parent: parent,
              material: material,
              centerSubmesh: centerSubmesh
            }); // Load the mesh.
            // Once the mesh is loaded, it will be stored on Gz3D.Scene.

            this.scene.loadMeshFromUri(modelUri, submesh, centerSubmesh, // onLoad
            function (mesh) {
              // Check for the pending meshes.
              for (var i = 0; i < that.pendingMeshes.length; i++) {
                if (that.pendingMeshes[i].meshUri === mesh.name) {
                  // No submesh: Load the result.
                  if (!that.pendingMeshes[i].submesh) {
                    loadMesh(mesh, that.pendingMeshes[i].material, that.pendingMeshes[i].parent, ext);
                  } else {
                    // Check if the mesh belongs to a submesh.
                    var allChildren = [];
                    getDescendants(mesh, allChildren);

                    for (var c = 0; c < allChildren.length; ++c) {
                      if (allChildren[c] instanceof THREE__namespace.Mesh) {
                        if (allChildren[c].name === that.pendingMeshes[i].submesh) {
                          loadMesh(mesh, that.pendingMeshes[i].material, that.pendingMeshes[i].parent, ext);
                        } else {
                          // The mesh is already stored in Scene.
                          // The new submesh will be parsed.
                          that.scene.loadMeshFromUri(mesh.name, that.pendingMeshes[i].submesh, that.pendingMeshes[i].centerSubmesh, // on load
                          function (mesh) {
                            loadMesh(mesh, that.pendingMeshes[i].material, that.pendingMeshes[i].parent, ext);
                          }, // on error
                          function (error) {
                            console.error("Mesh loading error", error);
                          });
                        }
                      }
                    }
                  }
                }
              }
            }, // onError
            function (error) {
              console.error("Mesh loading error", modelUri);
            });
          }
        } else if (geom.heightmap) {
          this.scene.loadHeightmap(geom.heightmap.heights, geom.heightmap.size.x, geom.heightmap.size.y, geom.heightmap.width, geom.heightmap.height, new THREE__namespace.Vector3(geom.heightmap.origin.x, geom.heightmap.origin.y, geom.heightmap.origin.z), geom.heightmap.texture, geom.heightmap.blend, parent);
        }

        if (obj) {
          if (material) {
            // texture mapping for simple shapes and planes only,
            // not used by mesh and terrain
            this.scene.setMaterial(obj, material);
          }

          obj.updateMatrix();
          parent.add(obj);
          loadGeom(parent);
        } // Callback function when the mesh is ready.


        function loadMesh(mesh, material, parent, ext) {
          if (!mesh) {
            console.error("Failed to load mesh.");
            return;
          } // Note: This material is the one created by the createMaterial method,
          // which is the material defined by the SDF file or the material script.


          if (material) {
            // Because the stl mesh doesn't have any children we cannot set
            // the materials like other mesh types.
            if (ext !== ".stl") {
              var allChildren = [];
              getDescendants(mesh, allChildren);

              for (var c = 0; c < allChildren.length; ++c) {
                if (allChildren[c] instanceof THREE__namespace.Mesh) {
                  // Some Collada files load their own textures.
                  // If the mesh already has a material with
                  // a texture, we skip this step (but only if there is no
                  // PBR materials involved).
                  var isColladaWithTexture = ext === ".dae" && !!allChildren[c].material && !!allChildren[c].material.map;

                  if (!isColladaWithTexture || material.pbr) {
                    that.scene.setMaterial(allChildren[c], material);
                    break;
                  }
                }
              }
            } else {
              that.scene.setMaterial(mesh, material);
            }
          } else {
            // By default, the STL Loader creates meshes with a basic material with a random color.
            // If no material is set via the SDF file, provide a more appropriate one.
            if (ext === ".stl") {
              that.scene.setMaterial(mesh, {
                ambient: [1, 1, 1, 1]
              });
            }
          }

          parent.add(mesh.clone());
          loadGeom(parent);
        }

        function loadGeom(visualObj) {
          var allChildren = [];
          getDescendants(visualObj, allChildren);

          for (var c = 0; c < allChildren.length; ++c) {
            if (allChildren[c] instanceof THREE__namespace.Mesh) {
              allChildren[c].castShadow = true;
              allChildren[c].receiveShadow = true;

              if (visualObj.castShadow) {
                allChildren[c].castShadow = visualObj.castShadow;
              }

              if (visualObj.receiveShadow) {
                allChildren[c].receiveShadow = visualObj.receiveShadow;
              }

              if (visualObj.name.indexOf("COLLISION_VISUAL") >= 0) {
                allChildren[c].castShadow = false;
                allChildren[c].receiveShadow = false;
                allChildren[c].visible = that.scene.showCollisions;
              }

              break;
            }
          }
        }
      }
      /**
       * Parses SDF visual element and creates THREE 3D object by parsing
       * geometry element using createGeom function
       * @param {object} visual - SDF visual element
       * @param {object} options - Options to send to the creation process.
       * It can include:
       *   - enableLights - True to have lights visible when the object is created.
       *                    False to create the lights, but set them to invisible
       *                    (off).
       *   - fuelName - Name of the resource in Fuel. Helps to match URLs to the
       *                correct path. Requires 'fuelOwner'.
       *   - fuelOwner - Name of the resource's owner in Fuel. Helps to match URLs
       *                 to the correct path. Requires 'fuelName'.
       * @returns {THREE.Object3D} visualObj - 3D object which is created
       * according to SDF visual element.
       */

    }, {
      key: "createVisual",
      value: function createVisual(visual, options) {
        var visualObj = new THREE__namespace.Object3D(); //TODO: handle these node values
        // cast_shadow, receive_shadows

        if (visual.geometry) {
          visualObj.name = visual["@name"] || visual["name"];

          if (visual.pose) {
            var visualPose = this.parsePose(visual.pose);
            this.scene.setPose(visualObj, visualPose.position, visualPose.orientation);
          }

          this.createGeom(visual.geometry, visual.material, visualObj, options);
        }

        return visualObj;
      }
      /**
       * Parses SDF sensor element and creates THREE 3D object
       * @param {object} sensor - SDF sensor element
       * @param {object} options - Options to send to the creation process.
       * It can include:
       *  - fuelName - Name of the resource in Fuel. Helps to match URLs to the
       *               correct path. Requires 'fuelOwner'.
       *  - fuelOwner - Name of the resource's owner in Fuel. Helps to match URLs
       *                to the correct path. Requires 'fuelName'.
       * @returns {THREE.Object3D} sensorObj - 3D object which is created
       * according to SDF sensor element.
       */

    }, {
      key: "createSensor",
      value: function createSensor(sensor, options) {
        var sensorObj = new THREE__namespace.Object3D();
        sensorObj.name = sensor["name"] || sensor["@name"] || "";

        if (sensor.pose) {
          var sensorPose = this.parsePose(sensor.pose);
          this.scene.setPose(sensorObj, sensorPose.position, sensorPose.orientation);
        }

        return sensorObj;
      }
      /**
       * Parses an object and spawns the given 3D object.
       * @param {object} obj - The object, obtained after parsing the SDF or from
       * a world message.
       * @param {object} options - Options to send to the creation process.
       * It can include:
       *  - enableLights - True to have lights visible when the object is created.
       *                   False to create the lights, but set them to invisible
       *                   (off).
       *  - fuelName - Name of the resource in Fuel. Helps to match URLs to the
       *               correct path. Requires 'fuelOwner'.
       *  - fuelOwner - Name of the resource's owner in Fuel. Helps to match URLs
       *                to the correct path. Requires 'fuelName'.
       * @returns {THREE.Object3D} object - 3D object which is created from the
       * given object.
       */

    }, {
      key: "spawnFromObj",
      value: function spawnFromObj(obj, options) {
        if (obj.model) {
          return this.spawnModelFromSDF(obj, options);
        } else if (obj.light) {
          return this.spawnLight(obj);
        } else if (obj.world) {
          return this.spawnWorldFromSDF(obj, options);
        }

        console.error("Unable to spawn from obj", obj);
        return new THREE__namespace.Object3D();
      }
      /**
       * Parses SDF XML string or SDF XML DOM object and return the created Object3D
       * @param {object} sdf - It is either SDF XML string or SDF XML DOM object
       * @returns {THREE.Object3D} object - 3D object which is created from the
       * given SDF.
       */

    }, {
      key: "spawnFromSDF",
      value: function spawnFromSDF(sdf) {
        var sdfObj = this.parseSDF(sdf);
        return this.spawnFromObj(sdfObj, {
          enableLights: true
        });
      }
      /**
       * Parses SDF XML string or SDF XML DOM object
       * @param {object} sdf - It is either SDF XML string or SDF XML DOM object
       * @returns {object} object - The parsed SDF object.
       */

    }, {
      key: "parseSDF",
      value: function parseSDF(sdf) {
        // SDF as a string.
        var sdfString;

        if (typeof sdf === "string") {
          sdfString = sdf;
        } else {
          var serializer = new XMLSerializer();
          sdfString = serializer.serializeToString(sdf);
        }

        var options = {
          ignoreAttributes: false,
          attributeNamePrefix: "@",
          htmlEntities: true
        };
        var sdfObj;
        var parser = new fastXmlParser.XMLParser(options);
        var validation = fastXmlParser.XMLValidator.validate(sdfString, options); // Validator returns true or an error object.

        if (validation === true) {
          sdfObj = parser.parse(sdfString).sdf;
        } else {
          console.error("Failed to parse SDF: ", validation.err);
          return;
        }

        return sdfObj;
      }
      /**
       * Loads SDF file according to given name.
       * @param {string} sdfName - Either name of model / world or the filename
       * @param {function} callback - The callback to use once the SDF file is ready.
       */

    }, {
      key: "loadSDF",
      value: function loadSDF(sdfName, callback) {
        if (!sdfName) {
          var m = "Must provide either a model/world name or the URL of an SDF file";
          console.error(m);
          return;
        }

        var lowerCaseName = sdfName.toLowerCase();
        var filename = ""; // In case it is a full URL

        if (lowerCaseName.indexOf("http") === 0) {
          filename = sdfName;
        } // In case it is just the model/world name, look for it on the default URL
        else {
          if (lowerCaseName.endsWith(".world") || lowerCaseName.endsWith(".sdf")) {
            filename = this.MATERIAL_ROOT + "/worlds/" + sdfName;
          } else {
            filename = this.MATERIAL_ROOT + "/" + sdfName + "/model.sdf";
          }
        }

        if (!filename) {
          console.error("Error: unable to load " + sdfName + " - file not found");
          return;
        }

        var that = this;
        this.fileFromUrl(filename, function (sdf) {
          if (!sdf) {
            console.error("Error: Failed to get the SDF file (" + filename + "). The XML is likely invalid.");
            return;
          }

          callback(that.spawnFromSDF(sdf));
        });
      }
      /**
       * Creates 3D object from parsed model SDF
       * @param {object} sdfObj - parsed SDF object
       * @param {object} options - Options to send to the creation process.
       * It can include:
       *  - enableLights - True to have lights visible when the object is created.
       *                   False to create the lights, but set them to invisible (off).
       *  - fuelName - Name of the resource in Fuel. Helps to match URLs to the correct path. Requires 'fuelOwner'.
       *  - fuelOwner - Name of the resource's owner in Fuel. Helps to match URLs to the correct path. Requires 'fuelName'.
       * @returns {THREE.Object3D} modelObject - 3D object which is created
       * according to SDF model object.
       */

    }, {
      key: "spawnModelFromSDF",
      value: function spawnModelFromSDF(sdfObj, options) {
        var _this = this;

        // create the model
        var modelObj = new THREE__namespace.Object3D();
        modelObj.name = sdfObj.model["name"] || sdfObj.model["@name"];
        var pose;
        var i;
        var linkObj;

        if (sdfObj.model.pose) {
          pose = this.parsePose(sdfObj.model.pose);
          this.scene.setPose(modelObj, pose.position, pose.orientation);
        } //convert link object to link array


        if (sdfObj.model.link) {
          if (!(sdfObj.model.link instanceof Array)) {
            sdfObj.model.link = [sdfObj.model.link];
          }

          for (i = 0; i < sdfObj.model.link.length; ++i) {
            linkObj = this.createLink(sdfObj.model.link[i], options);

            if (linkObj) {
              modelObj.add(linkObj);
            }
          }
        } //convert nested model objects to model array


        if (sdfObj.model.model) {
          if (!(sdfObj.model.model instanceof Array)) {
            sdfObj.model.model = [sdfObj.model.model];
          }

          for (i = 0; i < sdfObj.model.model.length; ++i) {
            var tmpModelObj = {
              model: sdfObj.model.model[i]
            };
            var nestedModelObj = this.spawnModelFromSDF(tmpModelObj, options);

            if (nestedModelObj) {
              modelObj.add(nestedModelObj);
            }
          }
        } // Parse included models.


        if (sdfObj.model.include) {
          // Convert to array.
          if (!(sdfObj.model.include instanceof Array)) {
            sdfObj.model.include = [sdfObj.model.include];
          } // Ignore linter warnings. We use arrow functions to avoid binding 'this'.


          sdfObj.model.include.forEach(function (includedModel) {
            _this.includeModel(includedModel, modelObj);
          });
        }

        return modelObj;
      }
      /**
       * Creates 3D object from parsed world SDF
       * @param {object} sdfObj - parsed SDF object
       * @param {object} options - Options to send to the creation process.
       * It can include:
       *   - enableLights - True to have lights visible when the object is created.
       *                    False to create the lights, but set them to invisible (off).
       *   - fuelName - Name of the resource in Fuel. Helps to match URLs to the correct path. Requires 'fuelOwner'.
       *   - fuelOwner - Name of the resource's owner in Fuel. Helps to match URLs to the correct path. Requires 'fuelName'.
       * @returns {THREE.Object3D} worldObject - 3D object which is created
       * according to SDF world object.
       */

    }, {
      key: "spawnWorldFromSDF",
      value: function spawnWorldFromSDF(sdfObj, options) {
        var _this2 = this;

        var worldObj = new THREE__namespace.Object3D();
        worldObj.name = this.createUniqueName(sdfObj.world); // remove default sun before adding objects
        // we will let the world file create its own light

        var sun = this.scene.getByName("sun");

        if (sun) {
          this.scene.remove(sun);
        } // parse models


        if (sdfObj.world.model) {
          // convert object to array
          if (!(sdfObj.world.model instanceof Array)) {
            sdfObj.world.model = [sdfObj.world.model];
          }

          for (var j = 0; j < sdfObj.world.model.length; ++j) {
            var tmpModelObj = {
              model: sdfObj.world.model[j]
            };
            var modelObj = this.spawnModelFromSDF(tmpModelObj, options);
            worldObj.add(modelObj);
          }
        } // parse lights


        if (sdfObj.world.light) {
          // convert object to array
          if (!(sdfObj.world.light instanceof Array)) {
            sdfObj.world.light = [sdfObj.world.light];
          }

          for (var k = 0; k < sdfObj.world.light.length; ++k) {
            var lightObj = this.spawnLight(sdfObj.world.light[k]);

            if (lightObj !== null && lightObj !== undefined) {
              if (options && options.enableLights) {
                lightObj.visible = options.enableLights;
              }

              worldObj.add(lightObj);
            }
          }
        } // Parse included models.


        if (sdfObj.world.include) {
          // Convert to array.
          if (!(sdfObj.world.include instanceof Array)) {
            sdfObj.world.include = [sdfObj.world.include];
          } // Ignore linter warnings. We use arrow functions to avoid binding 'this'.


          sdfObj.world.include.forEach(function (includedModel) {
            _this2.includeModel(includedModel, worldObj);
          });
        }

        return worldObj;
      }
      /**
       * Auxiliary function to get and parse an included model.
       * To render an included model, we need to request its files to the Server.
       * A cache map is used to avoid making duplicated requests and reuse the obtained SDF.
       * @param {object} includedModel - The included model.
       * @param {THREE.Object3D} parent - The parent that is including the given model.
       */

    }, {
      key: "includeModel",
      value: function includeModel(includedModel, parent) {
        var _this3 = this;

        // Suppress linter warnings. This shouldn't be necessary after
        // switching to es6 or more.
        // The included model is copied. This allows the SDF to be reused
        // without modifications. The parent is stored in the model, so we
        // don't lose their context once the model's Object3D is created.
        var model = Object.assign(Object.assign({}, includedModel), {
          parent: parent
        }); // We need to request the files of the model to the Server.
        // In order to avoid duplicated requests, we store the model in an
        // array until their files are available.

        if (!this.pendingModels.has(model.uri)) {
          // The URI is not in the cache map. We have to make the request to
          // the Server. Add the model to the models array of the map, to use
          // them once the request resolves.
          this.pendingModels.set(model.uri, {
            models: [model]
          }); // Request the files from the server, and create the pending
          // models on it's callback.

          if (this.requestHeaderKey && this.requestHeaderValue) {
            this.fuelServer.setRequestHeader(this.requestHeaderKey, this.requestHeaderValue);
          }

          this.fuelServer.getFiles(model.uri, function (files) {
            // The files were obtained.
            var sdfUrl = "";
            files.forEach(function (file) {
              if (file.endsWith("model.sdf")) {
                sdfUrl = file;
                return;
              }

              _this3.addUrl(file);
            }); // Read and parse the SDF.

            _this3.fileFromUrl(sdfUrl, function (sdf) {
              if (!sdf) {
                console.error("Error: Failed to get the SDF file (" + sdfUrl + "). The XML is likely invalid.");
                return;
              }

              var sdfObj = _this3.parseSDF(sdf);

              var entry = _this3.pendingModels.get(model.uri);

              entry.sdf = sdfObj; // Extract Fuel owner and name. Used to match the correct URL.

              var options;

              if (model.uri.startsWith("https://") || model.uri.startsWith("file://")) {
                var uriSplit = model.uri.split("/");
                var modelsIndex = uriSplit.indexOf("models");
                options = {
                  fuelOwner: uriSplit[modelsIndex - 1],
                  fuelName: uriSplit[modelsIndex + 1]
                };
              }

              entry.models.forEach(function (pendingModel) {
                // Create the Object3D.
                var modelObj = _this3.spawnFromObj(sdfObj, options); // Set name.


                if (pendingModel.name) {
                  modelObj.name = pendingModel.name;
                } // Set pose.


                if (pendingModel.pose) {
                  var pose = _this3.parsePose(pendingModel.pose);

                  _this3.scene.setPose(modelObj, pose.position, pose.orientation);
                } // Add to parent.


                pendingModel.parent.add(modelObj);
              }); // Cleanup: Remove the list of models.

              entry.models = [];
            });
          });
        } else {
          // The URI was received already. Push the model into the pending models array.
          var entry = this.pendingModels.get(model.uri);
          entry.models.push(model); // If the SDF was already obtained, apply it to this model.

          if (entry.sdf) {
            // Extract Fuel owner and name. Used to match the correct URL.
            var options;

            if (model.uri.startsWith("https://") || model.uri.startsWith("file://")) {
              var uriSplit = model.uri.split("/");
              var modelsIndex = uriSplit.indexOf("models");
              options = {
                fuelOwner: uriSplit[modelsIndex - 1],
                fuelName: uriSplit[modelsIndex + 1]
              };
            }

            entry.models.forEach(function (pendingModel) {
              var sdfObj = entry.sdf;

              var modelObj = _this3.spawnFromObj(sdfObj, options); // Set name.


              if (pendingModel.name) {
                modelObj.name = pendingModel.name;
              } // Set pose.


              if (pendingModel.pose) {
                var pose = _this3.parsePose(pendingModel.pose);

                _this3.scene.setPose(modelObj, pose.position, pose.orientation);
              } // Add to parent.


              pendingModel.parent.add(modelObj);
            }); // Cleanup: Remove the list of models.

            entry.models = [];
          }
        }
      }
      /**
       * Creates a link 3D object of the model. A model consists of links
       * these links are 3D objects. The function creates only visual elements
       * of the link by createLink function
       * @param {object} link - parsed SDF link object
       * @param {object} options - Options to send to the creation process. It can include:
       *                 - enableLights - True to have lights visible when the object is created.
       *                                  False to create the lights, but set them to invisible (off).
       *                 - fuelName - Name of the resource in Fuel. Helps to match URLs to the correct path. Requires 'fuelOwner'.
       *                 - fuelOwner - Name of the resource's owner in Fuel. Helps to match URLs to the correct path. Requires 'fuelName'.
       * @returns {THREE.Object3D} linkObject - 3D link object
       */

    }, {
      key: "createLink",
      value: function createLink(link, options) {
        var linkPose;
        var visualObj;
        var sensorObj;
        var linkObj = new THREE__namespace.Object3D();
        linkObj.name = link["name"] || link["@name"] || "";

        if (link.inertial) {
          var inertialPose;
          var inertialMass;
          var inertia = new Inertia();
          linkObj.userData.inertial = {};
          inertialPose = link.inertial.pose;
          inertialMass = link.inertial.mass;
          inertia.ixx = link.inertial.ixx;
          inertia.ixy = link.inertial.ixy;
          inertia.ixz = link.inertial.ixz;
          inertia.iyy = link.inertial.iyy;
          inertia.iyz = link.inertial.iyz;
          inertia.izz = link.inertial.izz;
          linkObj.userData.inertial.inertia = inertia;

          if (inertialMass) {
            linkObj.userData.inertial.mass = inertialMass;
          }

          if (inertialPose) {
            linkObj.userData.inertial.pose = inertialPose;
          }
        }

        if (link.pose) {
          linkPose = this.parsePose(link.pose);
          this.scene.setPose(linkObj, linkPose.position, linkPose.orientation);
        }

        if (link.visual) {
          if (!(link.visual instanceof Array)) {
            link.visual = [link.visual];
          }

          for (var i = 0; i < link.visual.length; ++i) {
            visualObj = this.createVisual(link.visual[i], options);

            if (visualObj && !visualObj.parent) {
              linkObj.add(visualObj);
            }
          }
        }

        if (link.collision) {
          if (!(link.collision instanceof Array)) {
            link.collision = [link.collision];
          }

          for (var j = 0; j < link.collision.length; ++j) {
            visualObj = this.createVisual(link.collision[j], options);

            if (visualObj && !visualObj.parent) {
              visualObj.castShadow = false;
              visualObj.receiveShadow = false;
              visualObj.visible = this.scene.showCollisions;
              linkObj.add(visualObj);
            }
          }
        }

        if (link.light) {
          if (!(link.light instanceof Array)) {
            link.light = [link.light];
          }

          for (var k = 0; k < link.light.length; ++k) {
            var light = this.spawnLight(link.light[k]);

            if (light !== null && light !== undefined) {
              if (options && options.enableLights !== undefined) {
                light.visible = options.enableLights;
              }

              light.userData = {
                type: "light"
              };
              linkObj.add(light);
            }
          }
        }

        if (link.particle_emitter) {
          if (!(link.particle_emitter instanceof Array)) {
            link.particle_emitter = [link.particle_emitter];
          }

          for (var em = 0; em < link.particle_emitter.length; ++em) {
            var emitter = this.createParticleEmitter(link.particle_emitter[em], linkObj);

            if (emitter !== null && emitter !== undefined) {
              linkObj.userData = {
                emitter: emitter
              };
              linkObj.add(emitter);
            }
          }
        }

        if (link.sensor) {
          if (!(link.sensor instanceof Array)) {
            link.sensor = [link.sensor];
          }

          for (var sidx = 0; sidx < link.sensor.length; ++sidx) {
            sensorObj = this.createSensor(link.sensor[sidx], options);

            if (sensorObj && !sensorObj.parent) {
              linkObj.add(sensorObj);
            }
          }
        }

        return linkObj;
      }
      /**
       * Creates the Particle Emitter.
       *
       * @param {object} Emitter. The emitter element from SDF or protobuf object.
       * @param {THREE.Object3D} Parent. The link that contains the emitter.
       * @return {THREE.Object3D} A THREE.Object3D that contains the particle emitter.
       */

    }, {
      key: "createParticleEmitter",
      value: function createParticleEmitter(emitter, parent) {
        // Particle Emitter is handled with Three Nebula, a third-party library.
        // More information at https://github.com/creativelifeform/three-nebula
        // Auxliar function to extract the value of an emitter property from
        // either SDF or protobuf object (stored in a data property).
        function extractValue(property) {
          if (emitter && emitter[property] !== undefined) {
            if (emitter[property].data !== undefined) {
              // The Message Prototype has data, but if not specified, it uses a default
              // value (like 0 or false). We want only explicitly set data, which we get by converting
              // the message to JSON.
              var value = emitter[property];
              var valueJson = value.toJSON();
              return valueJson.data;
            } else {
              return emitter[property];
            }
          }

          return undefined;
        }

        var particleEmitterObj = new THREE__namespace.Object3D(); // Given name of the emitter.

        this.createUniqueName(emitter); // Whether the emitter is generating particles or not.

        var emitting = this.parseBool(extractValue("emitting")) || false; // Duration of the particle emitter. Infinite if null.

        extractValue("duration");

        extractValue("type") || extractValue("@type") || "point"; // Lifetime of the individual particles, in seconds.

        var extractedLifetime = extractValue("lifetime");
        var lifetime = extractedLifetime !== undefined ? parseFloat(extractedLifetime) : 5; // Velocity range.

        var extractedMinVelocity = extractValue("min_velocity");
        var minVelocity = extractedMinVelocity !== undefined ? parseFloat(extractedMinVelocity) : 1;
        var extractedMaxVelocity = extractValue("max_velocity");
        var maxVelocity = extractedMaxVelocity !== undefined ? parseFloat(extractedMaxVelocity) : 1; // Size of the particle emitter.
        // The SDF particle emitter spec lists size as
        // [x: width, y: height, z: depth].

        var extractedSize = extractValue("size");
        var size = this.parse3DVector(extractedSize) || new THREE__namespace.Vector3(1, 1, 1); // Size of the individual particles.

        var extractedParticleSize = extractValue("particle_size");
        var particleSize = this.parse3DVector(extractedParticleSize) || new THREE__namespace.Vector3(1, 1, 1); // Pose of the particle emitter

        var extractedPose = extractValue("pose");
        this.parsePose(extractedPose); // Particles per second emitted.

        var extractedRate = extractValue("rate");
        var rate = extractedRate !== undefined ? parseFloat(extractedRate) : 10; // Scale modifier for each particle. Modifies their size per second.

        var extractedScaleRate = extractValue("scale_rate");
        var scaleRate = extractedScaleRate !== undefined ? parseFloat(extractedScaleRate) : 1; // Material

        var particleMaterial = extractValue("material");
        var particleTextureUrl = particleMaterial.pbr.albedo_map;
        var particleTexture = this.scene.loadTexture(particleTextureUrl); // Create a Nebula Emitter.

        var nebulaEmitter = new System.Emitter(); // Create the Nebula System, if needed.
        // We need only one system regardless of the amount of emitter we have.

        var nebulaSystem = this.scene.getParticleSystem();
        var nebulaRenderer = this.scene.getParticleRenderer();

        if (!nebulaSystem) {
          nebulaSystem = new System__default["default"](); // Note: We pass the global THREE object here, but we could pass an object with just the
          // THREE methods it uses.
          // See https://github.com/creativelifeform/three-nebula/tree/master/src/renderer

          nebulaRenderer = new System.SpriteRenderer(this.scene.scene, THREE__namespace);
          nebulaSystem.addRenderer(nebulaRenderer);
          this.scene.setupParticleSystem(nebulaSystem, nebulaRenderer);
        } // Initializers
        // Create the particle sprite and body.


        var createSprite = function createSprite() {
          var map = particleTexture;
          var material = new THREE__namespace.SpriteMaterial({
            map: map,
            transparent: true
          });
          return new THREE__namespace.Sprite(material);
        };

        var bodyInitializer = new System.Body(createSprite()); // Emitter's size
        // Note: Only Box type supported for now.

        var positionInitializer = new System.Position();
        var boxZone = new System.BoxZone(size.x, size.y, size.z);
        positionInitializer.addZone(boxZone);
        var particleLifetimeInitializer = new System.Life(lifetime); // Since rate is particles per second, we emit 1 particle per (1 / rate) seconds.

        var particleRate = new System.Rate(1, 1 / rate);
        var particleSizeInitializer = new System.Radius(particleSize.x, particleSize.y);
        var particleVelocityInitializer = new System.VectorVelocity(new THREE__namespace.Vector3(1, 0, 0), 0);
        particleVelocityInitializer.radiusPan = new System.Span(minVelocity, maxVelocity);
        var scaleBehaviour = new System.Scale( // Starting scale factor.
        1, // Ending scale factor. Since Scale Rate is scale change per second,
        //we roughly calculate the scale factor at the end of the particle's life.
        Math.pow(scaleRate, lifetime)); // Explicity avoid damping, otherwise particles will be slowed down.

        nebulaEmitter.damping = 0;
        nebulaEmitter.setRate(particleRate).addInitializers([positionInitializer, particleLifetimeInitializer, bodyInitializer, particleVelocityInitializer, particleSizeInitializer]).setPosition(parent.position).setRotation(parent.rotation);

        if (scaleRate !== 1) {
          nebulaEmitter.addBehaviour(scaleBehaviour);
        }

        if (emitting) {
          nebulaEmitter.emit();
        }

        nebulaSystem.addEmitter(nebulaEmitter).emit({
          onStart: function onStart() {},
          onUpdate: function onUpdate() {},
          onEnd: function onEnd() {}
        });
        return particleEmitterObj;
      }
      /**
       * Creates 3D object according to model name and type of the model and add
       * the created object to the scene.
       * @param {THREE.Object3D} model - model object which will be added to scene
       * @param {string} type - type of the model which can be followings: box,
       * sphere, cylinder, spotlight, directionallight, pointlight
       */

    }, {
      key: "addModelByType",
      value: function addModelByType(model, type) {
        var sdf;
        var translation = new THREE__namespace.Vector3();
        var quaternion = new THREE__namespace.Quaternion();
        var modelObj;
        var that = this;

        if (model.matrixWorld) {
          var matrix = model.matrixWorld;
          var scale = new THREE__namespace.Vector3();
          matrix.decompose(translation, quaternion, scale);
        }

        var euler = new THREE__namespace.Euler();
        euler.setFromQuaternion(quaternion);

        if (type === "box") {
          sdf = this.createBoxSDF(translation, euler);
          modelObj = this.spawnFromSDF(sdf);
        } else if (type === "sphere") {
          sdf = this.createSphereSDF(translation, euler);
          modelObj = this.spawnFromSDF(sdf);
        } else if (type === "cylinder") {
          sdf = this.createCylinderSDF(translation, euler);
          modelObj = this.spawnFromSDF(sdf);
        } else if (type == "capsule") {
          sdf = this.createCapsuleSDF(translation, euler);
          modelObj = this.spawnFromSDF(sdf);
        } else if (type === "spotlight") {
          modelObj = this.scene.createLight(2);
          this.scene.setPose(modelObj, translation, quaternion);
        } else if (type === "directionallight") {
          modelObj = this.scene.createLight(3);
          this.scene.setPose(modelObj, translation, quaternion);
        } else if (type === "pointlight") {
          modelObj = this.scene.createLight(1);
          this.scene.setPose(modelObj, translation, quaternion);
        } else {
          this.loadSDF(type, function (sdfObj) {
            modelObj = new THREE__namespace.Object3D();
            modelObj.add(sdfObj);
            modelObj.name = model.name;
            that.scene.setPose(modelObj, translation, quaternion);
          });
        }

        var addModelFunc = function addModelFunc() {
          // check whether object is removed
          var obj = that.scene.getByName(modelObj.name);

          if (obj === undefined) {
            that.scene.add(modelObj);
          } else {
            setTimeout(addModelFunc, 100);
          }
        };

        setTimeout(addModelFunc, 100);
      }
      /**
       * Creates SDF string for simple shapes: box, cylinder, sphere, capsule.
       * @param {string} type - type of the model which can be followings: box,
       * sphere, cylinder, capsule
       * @param {THREE.Vector3} translation - denotes the x,y,z position
       * of the object
       * @param {THREE.Euler} euler - denotes the euler rotation of the object
       * @param {string} geomSDF - geometry element string of 3D object which is
       * already created according to type of the object
       * @returns {string} sdf - SDF string of the simple shape
       */

    }, {
      key: "createSimpleShapeSDF",
      value: function createSimpleShapeSDF(type, translation, euler, geomSDF) {
        var sdf;
        sdf = '<sdf version="' + this.SDF_VERSION + '">' + '<model name="' + type + '">' + "<pose>" + translation.x + " " + translation.y + " " + translation.z + " " + euler.x + " " + euler.y + " " + euler.z + "</pose>" + '<link name="link">' + "<inertial><mass>1.0</mass></inertial>" + '<collision name="collision">' + "<geometry>" + geomSDF + "</geometry>" + "</collision>" + '<visual name="visual">' + "<geometry>" + geomSDF + "</geometry>" + "<material>" + "<script>" + "<uri>file://media/materials/scripts/gazebo.material" + "</uri>" + "<name>Gazebo/Grey</name>" + "</script>" + "</material>" + "</visual>" + "</link>" + "</model>" + "</sdf>";
        return sdf;
      }
      /**
       * Creates SDF string of box geometry element
       * @param {THREE.Vector3} translation - the x,y,z position of
       * the box object
       * @param {THREE.Euler} euler - the euler rotation of the box object
       * @returns {string} geomSDF - geometry SDF string of the box
       */

    }, {
      key: "createBoxSDF",
      value: function createBoxSDF(translation, euler) {
        var geomSDF = "<box>" + "<size>1.0 1.0 1.0</size>" + "</box>";
        return this.createSimpleShapeSDF("box", translation, euler, geomSDF);
      }
      /**
       * Creates SDF string of sphere geometry element
       * @param {THREE.Vector3} translation - the x,y,z position of
       * the box object
       * @param {THREE.Euler} euler - the euler rotation of the box object
       * @returns {string} geomSDF - geometry SDF string of the sphere
       */

    }, {
      key: "createSphereSDF",
      value: function createSphereSDF(translation, euler) {
        var geomSDF = "<sphere>" + "<radius>0.5</radius>" + "</sphere>";
        return this.createSimpleShapeSDF("sphere", translation, euler, geomSDF);
      }
      /**
       * Creates SDF string of cylinder geometry element
       * @param {THREE.Vector3} translation - the x,y,z position of
       * the box object
       * @param {THREE.Euler} euler - the euler rotation of the cylinder object
       * @returns {string} geomSDF - geometry SDF string of the cylinder
       */

    }, {
      key: "createCylinderSDF",
      value: function createCylinderSDF(translation, euler) {
        var geomSDF = "<cylinder>" + "<radius>0.5</radius>" + "<length>1.0</length>" + "</cylinder>";
        return this.createSimpleShapeSDF("cylinder", translation, euler, geomSDF);
      }
      /**
       * Creates SDF string of capsule geometry element
       * @param {THREE.Vector3} translation - the x,y,z position of
       * the box object
       * @param {THREE.Euler} euler - the euler rotation of the capsule object
       * @returns {string} geomSDF - geometry SDF string of the capsule
       */

    }, {
      key: "createCapsuleSDF",
      value: function createCapsuleSDF(translation, euler) {
        var geomSDF = "<capsule>" + "<radius>0.5</radius>" + "<length>1.0</length>" + "</capsule>";
        return this.createSimpleShapeSDF("capsule", translation, euler, geomSDF);
      }
      /**
       * Set a request header for internal requests.
       * Parser uses XMLHttpRequest, which handle headers with key-value pairs instead of an object (like THREE uses).
       *
       * @param {string} header - The header to send in the request.
       * @param {string} value - The value to set to the header.
       */

    }, {
      key: "setRequestHeader",
      value: function setRequestHeader(header, value) {
        this.requestHeaderKey = header;
        this.requestHeaderValue = value;
      }
      /**
       * Download a file from url.
       * @param {string} url - full URL to an SDF file.
       * @param {function} callback - The callback to use once the file is ready.
       */

    }, {
      key: "fileFromUrl",
      value: function fileFromUrl(url, callback) {
        // The request is asynchronous. To avoid disrupting the current workflow too much, we use a callback.
        // TODO(germanmas): We should update and use async/await instead throughout the library.
        var xhttp = new XMLHttpRequest();
        xhttp.overrideMimeType("text/xml");
        xhttp.open("GET", url, true);

        if (this.requestHeaderKey && this.requestHeaderValue) {
          xhttp.setRequestHeader(this.requestHeaderKey, this.requestHeaderValue);
        }

        xhttp.onload = function () {
          if (xhttp.readyState === 4) {
            if (xhttp.status !== 200) {
              console.error("Failed to get URL [" + url + "]");
              return;
            }

            callback(xhttp.responseXML);
          }
        };

        xhttp.onerror = function (e) {
          console.error(xhttp.statusText);
        };

        try {
          xhttp.send();
        } catch (err) {
          console.error("Failed to get URL [" + url + "]: " + err.message);
          return;
        }
      }
    }, {
      key: "createUniqueName",
      value: function createUniqueName(obj) {
        var objectName = obj["name"] || obj["@name"] || "";
        var objectId = obj["id"] || obj["@id"] || "";
        return objectName + objectId;
      }
    }]);

    return SDFParser;
  }();

  /**
   * The Asset Viewer class allows clients to render and view simulation resources, such as
   * models and worlds.
   *
   * This requires all of the resource's related URLs, and there is no websocket connection involved
   * in this process.
   */

  var AssetViewer = /*#__PURE__*/function () {
    /**
     * Once the Asset Viewer is created, it will setup the scene and start the animation loop.
     *
     * @param config The Asset Viewer configuration options.
     */
    function AssetViewer(config) {
      _classCallCheck(this, AssetViewer);

      var _a;
      /**
       * Behavior subject used to communicate if a resource has been loaded or not.
       * Note: This will be true when the Object3D is created, not when it's meshes and textures
       * finish loading.
       */


      this.resourceLoaded$ = new rxjs.BehaviorSubject(false);
      /**
       * ID of the HTML element that will hold the rendering context.
       */

      this.elementId = "gz-scene";
      /**
       * For animation purposes. The timestamp of the previous render in milliseconds.
       */

      this.previousRenderTimestampMs = 0;
      /**
       * For animation purposes. The frame used to cancel the animation.
       */

      this.cancelAnimationFrame = 0;
      /**
       * The scaling basis used, if the model is scaled.
       */

      this.scalingBasis = 1;
      /**
       * Whether or not the model should be scaled.
       */

      this.shouldScaleModel = false;
      /**
       * Used to determine if the model is already scaled.
       */

      this.isScaled = false;
      /**
       * Whether or not PBR materials should be used.
       */

      this.shouldUsePBR = false;
      this.elementId = (_a = config.elementId) !== null && _a !== void 0 ? _a : "gz-scene";
      this.token = config.token;
      this.setupVisualization();

      if (this.scene && config.addModelLighting) {
        this.scene.addModelLighting();
      }

      this.shouldScaleModel = !!config.scaleModel;
      this.shouldUsePBR = !!config.enablePBR;
      this.animate();
    }
    /**
     * Destroy the scene.
     */


    _createClass(AssetViewer, [{
      key: "destroy",
      value: function destroy() {
        if (this.cancelAnimationFrame) {
          cancelAnimationFrame(this.cancelAnimationFrame);
        }

        this.previousRenderTimestampMs = 0;

        if (this.scene) {
          this.scene.cleanup();
        }
      }
      /**
       * Resize the scene, according to its container's size.
       */

    }, {
      key: "resize",
      value: function resize() {
        if (this.scene && this.sceneElement) {
          this.scene.setSize(this.sceneElement.clientWidth, this.sceneElement.clientHeight);
        }
      }
      /**
       * Position the camera to start visualizing the asset.
       */

    }, {
      key: "resetView",
      value: function resetView() {
        var _a;

        var camera = (_a = this.scene) === null || _a === void 0 ? void 0 : _a.camera;

        if (camera) {
          camera.position.x = this.scalingBasis * 1.1;
          camera.position.y = -this.scalingBasis * 1.4;
          camera.position.z = this.scalingBasis * 0.6;
          camera.rotation.x = 67 * Math.PI / 180;
          camera.rotation.y = 33 * Math.PI / 180;
          camera.rotation.z = 12 * Math.PI / 180;
        }
      }
      /**
       * Given all the resource URLs, look for its SDF file and render it.
       * The obtained Object3D will be added to the Scene.
       *
       * @param files All the resource's related URLs.
       */

    }, {
      key: "renderFromFiles",
      value: function renderFromFiles(files) {
        var _this = this;

        if (!this.scene || !this.sdfParser) {
          return;
        }

        this.sdfParser.usingFilesUrls = true;
        this.sdfParser.enablePBR = this.shouldUsePBR; // Look for SDF file.

        var sdfFile = files.find(function (file) {
          return file.endsWith(".sdf");
        }); // Add files to the Parser.

        files.forEach(function (file) {
          return _this.sdfParser.addUrl(file);
        });

        if (sdfFile) {
          this.sdfParser.loadSDF(sdfFile, function (obj) {
            var _a; // Object has finished loading.


            _this.resource = obj;
            (_a = _this.scene) === null || _a === void 0 ? void 0 : _a.add(obj);

            _this.resourceLoaded$.next(true);
          });
        }
      }
      /**
       * Auxiliary method to scale the model. We aim to have it's largest dimension
       * scaled to a power of 10 (scaling basis).
       */

    }, {
      key: "scaleModel",
      value: function scaleModel() {
        if (!this.resource) {
          return;
        } // Create a bounding box for the object and calculate its size and center.


        var boundingBox = new THREE.Box3().setFromObject(this.resource);

        if (boundingBox.isEmpty()) {
          return;
        }

        var size = new THREE.Vector3();
        var center = new THREE.Vector3();
        boundingBox.getSize(size);
        boundingBox.getCenter(center);
        var maxDimension = Math.max(size.x, size.y, size.z); // Translate and rescale.
        // The scaling basis is calculated using the maximum dimension. Allows us to scale large models.
        // It is a power of 10.

        this.scalingBasis = Math.pow(10, Math.trunc(maxDimension).toString().length - 1);
        var scale = this.scalingBasis / maxDimension;
        center.multiplyScalar(-scale);
        this.resource.position.x = center.x;
        this.resource.position.y = center.y;
        this.resource.position.z = center.z;
        this.resource.scale.x = scale;
        this.resource.scale.y = scale;
        this.resource.scale.z = scale; // Re-center camera and avoid subsequent calls to this method in the animation loop.

        this.isScaled = true;
        this.resetView();
      }
      /**
       * Prepare the Gzweb Scene and SDF Parser before anything is added.
       */

    }, {
      key: "setupVisualization",
      value: function setupVisualization() {
        this.scene = new Scene({
          shaders: new Shaders()
        });
        this.sdfParser = new SDFParser(this.scene);

        if (this.token) {
          var header = "Authorization";
          var value = "Bearer ".concat(this.token);
          this.scene.setRequestHeader(header, value);
          this.sdfParser.setRequestHeader(header, value);
        }

        if (window.document.getElementById(this.elementId)) {
          this.sceneElement = window.document.getElementById(this.elementId);
          this.sceneElement.appendChild(this.scene.getDomElement());
          this.resize();
        } else {
          console.error("Unable to find HTML element with an id of", this.elementId);
        }
      }
      /**
       * The animation loop.
       */

    }, {
      key: "animate",
      value: function animate() {
        var _this2 = this;

        if (!this.scene) {
          return;
        } // Scale the model on the animation loop.
        // Loading meshes is an asynchronous process, so after loading the SDF file, its bounding box may be empty.
        // This is done only once, after a mesh is loaded and the model's bounding box is not empty.


        if (this.resource !== undefined && this.shouldScaleModel && !this.isScaled) {
          this.scaleModel();
        }

        this.cancelAnimationFrame = requestAnimationFrame(function (timestampMs) {
          if (_this2.previousRenderTimestampMs === 0) {
            _this2.previousRenderTimestampMs = timestampMs;
          }

          _this2.animate();

          _this2.scene.render(timestampMs - _this2.previousRenderTimestampMs);

          _this2.previousRenderTimestampMs = timestampMs;
        });
      }
    }]);

    return AssetViewer;
  }();

  /**
   * Type that represents a topic to be subscribed. This allows communication between Components and
   * the Websocket service of a Simulation.
   */
  var Topic = /*#__PURE__*/_createClass(function Topic(name, cb) {
    _classCallCheck(this, Topic);

    this.name = name;
    this.cb = cb;
  });

  var AudioTopic = /*#__PURE__*/_createClass(function AudioTopic(name, trans) {
    _classCallCheck(this, AudioTopic);

    var audioMap = new Map();
    var topic = new Topic(name, function (msg) {
      var playback = false;
      var uri = ""; // Get the playback and uri information.

      for (var key in msg.params) {
        if (key === "playback") {
          playback = msg.params[key].bool_value;
        } else if (key === "uri") {
          uri = msg.params[key].string_value;
        }
      } // Control audio playback if the audio file is in the audio map.


      if (uri in audioMap) {
        var tuple = audioMap[uri];

        if (tuple[1]) {
          tuple[0].play();
        } else {
          tuple[0].pause();
        }

        tuple[1] = playback; // Otherwise, fetch the audio file
      } else {
        console.log("Getting audio file", uri); // Fetching of the asset via getAsset() below is asynchronous, meaning
        // that we could have requests for the same asset come in while we are
        // fetching it.  To prevent multiple downloads and playing of the
        // audio, add the uri to the map immediately with an empty object;
        // we'll replace that dummy object with a fully active one once
        // downloading the asset is complete.

        audioMap[uri] = [new Audio(), playback];
        trans.getAsset(uri, function (asset) {
          var audioSrc = "data:audio/mp3;base64," + binaryToBase64(asset);
          var audio = new Audio(audioSrc);
          audio.src = audioSrc;
          audioMap[uri][0] = audio;

          if (audioMap[uri][1]) {
            audio.play();
          }
        });
      }
    });
    trans.subscribe(topic);
  });

  var controllers = {};
  var onButtonCb = null;
  var onAxisCb = null;
  /**
   * Create a gamepad interface
   * @param {function} onButton - Function callback that accepts a controller
   * object and a button object. This function is called when a button is pressed.
   * @param {function} onAxis - Function callback that accepts a controller
   * object and an axis object. This function is called when a joystick axis is moved.
   */

  var Gamepad = /*#__PURE__*/_createClass(function Gamepad(onButton, onAxis) {
    _classCallCheck(this, Gamepad);

    onButtonCb = onButton;
    onAxisCb = onAxis; // Listen for gamepad connections.

    window.addEventListener("gamepadconnected", handleGamepadConnect); // Listen for gamepad disconnections.

    window.addEventListener("gamepaddisconnected", handleGamepadDisconnect); // Start the main processing event loop

    requestAnimationFrame(updateGamepads);
  });
  /** Main controller processing function. This function is called every
   * animation frame to poll for controller updates.
   */

  function updateGamepads() {
    // Scan for connected gamepads.
    scanGamepads(); // Process each controller

    for (var c in controllers) {
      var controller = controllers[c]; // Poll each button

      for (var b = 0; b < controller.gamepad.buttons.length; b++) {
        var button = controller.gamepad.buttons[b];

        if (controller.prevButtons[b] !== button.pressed) {
          // Note that we update the button *before* we call the user callback.
          // That's so that the user callback can, at its option, get the complete
          // current state of the controller by looking at the prevButtons.
          controller.prevButtons[b] = button.pressed;
          onButtonCb(controller, {
            index: b,
            pressed: button.pressed
          });
        }
      } // Poll each axis


      for (var i = 0; i < controller.gamepad.axes.length; i++) {
        var axis = controller.gamepad.axes[i];

        if (controller.prevAxes[i] !== axis) {
          // Note that we update the axis *before* we call the user callback.
          controller.prevAxes[i] = axis;
          onAxisCb(controller, {
            index: i,
            axis: axis
          });
        }
      }
    }

    requestAnimationFrame(updateGamepads);
  }
  /**
   * Poll for controllers. Some browsers use connection events, and others
   * require polling.
   */


  function scanGamepads() {
    var gamepads = navigator.getGamepads();

    for (var i = 0; i < gamepads.length; i++) {
      addGamepad(gamepads[i]);
    }
  }
  /** Adds or updates a gamepad to the list of controllers.
   * @param {object} The gamepad to add/update
   */


  function addGamepad(gamepad) {
    if (gamepad) {
      if (!(gamepad.index in controllers)) {
        console.log("Adding gamepad", gamepad.id);
        controllers[gamepad.index] = {
          gamepad: gamepad,
          prevButtons: new Array(gamepad.buttons.length),
          prevAxes: new Array(gamepad.axes.length)
        }; // Set button initial state

        for (var b = 0; b < gamepad.buttons.length; b++) {
          controllers[gamepad.index].prevButtons[b] = false;
        } // Set axes initial state


        for (var a = 0; a < gamepad.axes.length; a++) {
          controllers[gamepad.index].prevAxes[a] = 0.0;
        }
      } else {
        controllers[gamepad.index].gamepad = gamepad;
      }
    }
  }
  /** Removes a gamepad from the list of controllers
   * @param {object} The gamepad to remove
   */


  function removeGamepad(gamepad) {
    if (gamepad && gamepad.index in controllers) {
      delete controllers[gamepad.index];
    }
  }
  /** Gamepad connect callback handler
   * @param {event} The gamepad connect event.
   */


  function handleGamepadConnect(e) {
    addGamepad(e.gamepad);
  }
  /** Gamepad disconnect callback handler
   * @param {event} The gamepad disconnect event.
   */


  function handleGamepadDisconnect(e) {
    removeGamepad(e.gamepad);
  }

  /**
   * A Publisher is used to allow clients to publish messages to a particular topic.
   */
  var Publisher = /*#__PURE__*/function () {
    /**
     * This constructor should be called by Transport.
     *
     * @param topic The topic name to publish to.
     * @param msgTypeName The message type name to use.
     * @param def The protobuf message definition.
     * @param pub Function set by Transport in order to send the message through the websocket.
     */
    function Publisher(topic, msgTypeName, def, pub) {
      _classCallCheck(this, Publisher);

      this.topic = topic;
      this.msgTypeName = msgTypeName;
      this.messageDef = def;
      this.pubFunc = pub;
    }
    /**
     * Creates a new message using the specified properties.
     *
     * @param properties The propoerties to be set in the message.
     * @returns The message instance.
     */


    _createClass(Publisher, [{
      key: "createMessage",
      value: function createMessage(properties) {
        return this.messageDef.create(properties);
      }
      /**
       * Publish a message.
       *
       * @param msg The message to publish.
       */

    }, {
      key: "publish",
      value: function publish(msg) {
        // Serialized the message
        var buffer = this.messageDef.encode(msg).finish();
        var strBuf = new TextDecoder().decode(buffer); // Publish the message over the websocket

        this.pubFunc(this.topic, this.msgTypeName, strBuf);
      }
    }]);

    return Publisher;
  }();

  /**
   * The Transport class is in charge of managing the websocket connection to a
   * Gazebo websocket server.
   */

  var Transport = /*#__PURE__*/function () {
    function Transport() {
      _classCallCheck(this, Transport);

      /**
       * Scene Information behavior subject.
       * Components can subscribe to it to get the scene information once it is obtained.
       */
      this.sceneInfo$ = new rxjs.BehaviorSubject(null);
      /**
       * List of available topics.
       *
       * Array of objects containing {topic, msg_type}.
       */

      this.availableTopics = [];
      /**
       * Map of the subscribed topics.
       * - Key: The topic name.
       * - Value: The Topic object, which includes the callback.
       *
       * New subscriptions should be added to this map, in order to correctly derive the messages
       * received.
       */

      this.topicMap = new Map();
      /**
       * A map of asset uri to asset types. This allows a caller to request
       * an asset from the websocket server and receive a callback when the
       * aseset has been fetched.
       */

      this.assetMap = new Map();
      /**
       * The world that is being used in the Simulation.
       */

      this.world = "";
      /**
       * Status connection behavior subject.
       * Internally keeps track of the connection state.
       * Uses a Behavior Subject because it has an initial state and stores a value.
       */

      this.status$ = new rxjs.BehaviorSubject("disconnected");
    }
    /**
     * Connects to a websocket.
     *
     * @param url The url to connect to.
     * @param key Optional. A key to authorize access to the websocket messages.
     */


    _createClass(Transport, [{
      key: "connect",
      value: function connect(url, key) {
        var _this = this;

        // First, disconnect from previous connections.
        // This way we make sure that we only support one websocket connection.
        this.disconnect(); // Create the Websocket interface.

        this.ws = new WebSocket(url); // Set the handlers of the websocket events.

        this.ws.onopen = function () {
          return _this.onOpen(key);
        };

        this.ws.onclose = function () {
          return _this.onClose();
        };

        this.ws.onmessage = function (msgEvent) {
          return _this.onMessage(msgEvent);
        };

        this.ws.onerror = function (errorEvent) {
          return _this.onError(errorEvent);
        };
      }
      /**
       * Disconnects from a websocket.
       * Note: The cleanup should be done in the onclose event of the Websocket.
       */

    }, {
      key: "disconnect",
      value: function disconnect() {
        if (this.ws) {
          this.ws.close();
        }
      }
      /**
       * Advertise a topic.
       *
       * @param topic The topic to advertise.
       * @param msgTypeName The message type the topic will handle.
       * @returns The Publisher instance.
       */

    }, {
      key: "advertise",
      value: function advertise(topic, msgTypeName) {
        var _this2 = this;

        this.sendMessage(["adv", topic, msgTypeName, ""]);
        var msgDef = this.root.lookupType(msgTypeName);
        return new Publisher(topic, msgTypeName, msgDef, function (topic, msgTypeName, msg) {
          _this2.publish(topic, msgTypeName, msg);
        });
      }
      /**
       * Publish to a topic.
       *
       * @param topic The topic to publish to.
       * @param msgTypeName The message type.
       * @param msg The message to publish.
       */

    }, {
      key: "publish",
      value: function publish(topic, msgTypeName, msg) {
        this.sendMessage(["pub_in", topic, msgTypeName, msg]);
      }
      /**
       * Request a service.
       *
       * @param topic The service to request to.
       * @param msgTypeName The message type.
       * @param msg The message to publish. This should be a JSON representation
       * of the protobuf message.
       */

    }, {
      key: "requestService",
      value: function requestService(topic, msgTypeName, msgProperties) {
        if (!this.root) {
          console.error("Unable to request service - Message definitions are not ready");
          return;
        }

        var msgDef = this.root.lookupType(msgTypeName);

        if (!msgDef || msgDef === undefined) {
          console.error("Unable to lookup message type: ".concat(msgTypeName));
          return;
        }

        var msg = msgDef.create(msgProperties);

        if (!msg || msg === undefined) {
          console.error("Unable to create ".concat(msgTypeName, ", from, ").concat(msgProperties));
          return;
        } // Serialized the message


        var buffer = msgDef.encode(msg).finish();

        if (!buffer || buffer === undefined || buffer.length === 0) {
          console.error("Unable to serialize message.");
          return;
        }

        var strBuf = new TextDecoder().decode(buffer);
        this.sendMessage(["req", topic, msgTypeName, strBuf]);
      }
      /**
       * Subscribe to a topic.
       *
       * @param topic The topic to subscribe to.
       */

    }, {
      key: "subscribe",
      value: function subscribe(topic) {
        this.topicMap.set(topic.name, topic);
        var publisher = this.availableTopics.filter(function (pub) {
          return pub["topic"] === topic.name;
        })[0];

        if (publisher["msg_type"] === "ignition.msgs.Image" || publisher["msg_type"] === "gazebo.msgs.Image") {
          this.sendMessage(["image", topic.name, "", ""]);
        } else {
          this.sendMessage(["sub", topic.name, "", ""]);
        }
      }
      /**
       * Unsubscribe from a topic.
       *
       * @param name The name of the topic to unsubcribe from.
       */

    }, {
      key: "unsubscribe",
      value: function unsubscribe(name) {
        if (this.topicMap.has(name)) {
          var topic = this.topicMap.get(name);

          if (topic !== undefined && topic.unsubscribe !== undefined) {
            topic.unsubscribe();
          }

          this.topicMap["delete"](name);
          this.sendMessage(["unsub", name, "", ""]);
        }
      }
      /**
       * throttle the rate at which messages are published on a topic.
       *
       * @param topic The topic to throttle.
       * @param rate Publish rate.
       */

    }, {
      key: "throttle",
      value: function throttle(topic, rate) {
        this.sendMessage(["throttle", topic.name, "na", rate.toString()]);
      }
      /**
       * Return the list of available topics.
       *
       * @returns The list of topics that can be subscribed to.
       */

    }, {
      key: "getAvailableTopics",
      value: function getAvailableTopics() {
        return this.availableTopics;
      }
      /**
       * Return the list of subscribed topics.
       *
       * @returns A map containing the name and message type of topics that we are currently
       *          subscribed to.
       */

    }, {
      key: "getSubscribedTopics",
      value: function getSubscribedTopics() {
        return this.topicMap;
      }
      /**
       * Return the world.
       *
       * @returns The name of the world the websocket is connected to.
       */

    }, {
      key: "getWorld",
      value: function getWorld() {
        return this.world;
      }
      /**
       * Get an asset from Gazebo
       */

    }, {
      key: "getAsset",
      value: function getAsset(_uri, _cb) {
        var asset = {
          uri: _uri,
          cb: _cb
        };
        console.log("Getting asset via websocket - ".concat(_uri));
        this.assetMap.set(_uri, asset);
        this.sendMessage(["asset", "", "", _uri]);
      }
      /**
       * Send a message through the websocket. It verifies if the message is correct and if the
       * connection status allows it to be sent.
       *
       * @param msg The message to send. It consists of four parts:
       *   1. Operation
       *   2. Topic name
       *   3. Message type
       *   4. Payload
       */

    }, {
      key: "sendMessage",
      value: function sendMessage(msg) {
        // Verify the message has four parts.
        if (msg.length !== 4) {
          console.error("Message must have four parts", msg);
          return;
        } // Only send the message when the connection allows it.
        // Note: Some messages need to be sent during the connection process.


        var connectionStatus = this.status$.getValue();

        if (connectionStatus === "error") {
          console.error("Cannot send the message. Connection failed.", {
            status: connectionStatus,
            message: msg
          });
          return;
        } // In order to properly establish a connection, we need to send certain messages, such as
        // authentication messages, world name, etc.


        var operation = msg[0];

        if (operation === "auth" || operation === "protos" || operation === "topics-types" || operation === "worlds") {
          this.ws.send(this.buildMsg(msg));
          return;
        } // Other messages should be sent when the connection status is connected or ready.


        if (connectionStatus === "disconnected") {
          console.error("Trying to send a message but the websocket is disconnected.", msg);
          return;
        }

        this.ws.send(this.buildMsg(msg));
      }
      /**
       * Exposes the connection status as an Observable.
       */

    }, {
      key: "getConnectionStatus",
      value: function getConnectionStatus() {
        return this.status$.asObservable();
      }
      /**
       * Handler for the open event of a Websocket.
       *
       * @param key Optional. A key to authorize access to the websocket messages.
       */

    }, {
      key: "onOpen",
      value: function onOpen(key) {
        // An authorization key could be required to request the message definitions.
        if (key) {
          this.sendMessage(["auth", "", "", key]);
        } else {
          this.sendMessage(["protos", "", "", ""]);
        }
      }
      /**
       * Handler for the close event of a Websocket.
       *
       * Cleanup the connections.
       */

    }, {
      key: "onClose",
      value: function onClose() {
        this.topicMap.clear();
        this.availableTopics = [];
        this.root = null;
        this.status$.next("disconnected");
        this.sceneInfo$.next(null);
      }
      /**
       * Handler for the message event of a Websocket.
       *
       * Parses message responses from Gazebo and sends to the corresponding topic.
       */

    }, {
      key: "onMessage",
      value: function onMessage(event) {
        var _this3 = this;

        // If there is no Root, then handle authentication and the message definitions.
        var fileReader = new FileReader();

        if (!this.root) {
          fileReader.onloadend = function () {
            var content = fileReader.result; // Handle the response.

            switch (content) {
              case "authorized":
                // Get the message definitions.
                _this3.sendMessage(["protos", "", "", ""]);

                break;

              case "invalid":
                // TODO(germanmas) Throw a proper Unauthorized error.
                console.error("Invalid key");
                break;

              default:
                // Parse the message definitions.
                _this3.root = protobufjs.parse(fileReader.result, {
                  keepCase: true
                }).root; // Request topics.

                _this3.sendMessage(["topics-types", "", "", ""]); // Request world information.


                _this3.sendMessage(["worlds", "", "", ""]); // Now we can update the connection status.


                _this3.status$.next("connected");

                break;
            }
          };

          fileReader.readAsText(event.data);
          return;
        }

        fileReader.onloadend = function () {
          var _a, _b;

          if (!_this3.root) {
            console.error("Protobuf root has not been created");
            return;
          } // Return if at any point, the websocket connection is lost.


          if (_this3.status$.getValue() === "disconnected") {
            return;
          } // Decode as UTF-8 to get the header.


          var str = new TextDecoder("utf-8").decode(fileReader.result);
          var frameParts = str.split(",", 4);

          var msgType = _this3.root.lookup(frameParts[2]);

          var buffer = new Uint8Array(fileReader.result); // Decode the Message. The "+3" in the slice accounts for the commas in the frame.

          var msg; // get the actual msg payload without the header

          var msgData = buffer.slice(frameParts[0].length + frameParts[1].length + frameParts[2].length + 3); // do not decode image msg as it is raw compressed png data and not a
          // protobuf msg

          if (frameParts[2] === "ignition.msgs.Image" || frameParts[2] === "gazebo.msgs.Image") {
            msg = msgData;
          } else {
            msg = msgType.decode(msgData);
          } // For frame format information see the WebsocketServer documentation at:
          // https://github.com/gazebosim/gz-launch/blob/ign-launch5/plugins/websocket_server/WebsocketServer.hh


          if (frameParts[0] == "asset") {
            // Error to pass to the callback function, in order for the requester to handle it.
            var error; // Check for errors. We can check if the type is a string to avoid comapring with large assets.

            if (frameParts[2] === "ignition.msgs.StringMsg" || frameParts[2] === "gazebo.msgs.StringMsg") {
              switch (msg["data"]) {
                case AssetError.URI_MISSING:
                  console.error("Asset is missing an URI");
                  break;

                case AssetError.NOT_FOUND:
                  console.error("Asset not found via websocket - ".concat(frameParts[1])); // Set the error for the requester to handle.

                  error = AssetError.NOT_FOUND;
                  break;

                default:
                  console.error("Asset error:", msg["data"]);
                  break;
              } // There is no error for the requester.


              if (!error) {
                return;
              }
            } // Run the callback associated with the asset. This lets the requester
            // process the asset message.


            if (_this3.assetMap.has(frameParts[1])) {
              _this3.assetMap.get(frameParts[1]).cb(msg["data"], error);
            } else {
              console.error("No resource callback for ".concat(_this3.assetMap.get(frameParts[1]).uri));
            }
          } else if (frameParts[0] == "pub") {
            // Handle actions and messages.
            switch (frameParts[1]) {
              case "topics-types":
                var _iterator = _createForOfIteratorHelper(msg["publisher"]),
                    _step;

                try {
                  for (_iterator.s(); !(_step = _iterator.n()).done;) {
                    var pub = _step.value;

                    _this3.availableTopics.push(pub);
                  }
                } catch (err) {
                  _iterator.e(err);
                } finally {
                  _iterator.f();
                }

                break;

              case "topics":
                _this3.availableTopics = msg["data"];
                break;

              case "worlds":
                // The world name needs to be used to get the scene information.
                _this3.world = msg["data"][0];

                _this3.sendMessage(["scene", _this3.world, "", ""]);

                break;

              case "scene":
                // Emit the scene information. Contains all the models used.
                _this3.sceneInfo$.next(msg); // Once we received the Scene Information, we can start working.
                // We emit the Ready status to reflect this.


                _this3.status$.next("ready");

                break;

              default:
                // Message from a subscribed topic. Get the topic and execute its
                // callback.
                if (_this3.topicMap.has(frameParts[1])) {
                  (_b = (_a = _this3 === null || _this3 === void 0 ? void 0 : _this3.topicMap) === null || _a === void 0 ? void 0 : _a.get(frameParts[1])) === null || _b === void 0 ? void 0 : _b.cb(msg);
                }

                break;
            }
          } else if (frameParts[0] == "req") ; else {
            console.warn("Unhandled websocket message with frame operation", frameParts[0]);
          }
        }; // Read the blob data as an array buffer.


        fileReader.readAsArrayBuffer(event.data);
        return;
      }
      /**
       * Handler for the error event of a Websocket.
       */

    }, {
      key: "onError",
      value: function onError(event) {
        this.status$.next("error");
        this.disconnect();
        console.error(event);
      }
      /**
       * Helper function to build a message.
       * The message is a comma-separated string consisting in four parts:
       * 1. Operation
       * 2. Topic name
       * 3. Message type
       * 4. Payload
       */

    }, {
      key: "buildMsg",
      value: function buildMsg(parts) {
        return parts.join(",");
      }
    }]);

    return Transport;
  }();

  /**
   * SceneManager handles the interface between a Gazebo server and the
   * rendering scene. A user of gzweb will typically create a SceneManager and
   * then connect the SceneManager to a Gazebo server's websocket.
   *
   * This example will connect to a Gazebo server's websocket at WS_URL, and
   * start the rendering process. Rendering output will be placed in the HTML
   * element with the id ELEMENT_ID
   *
   * ```
   * let sceneMgr = new SceneManager(ELEMENT_ID, WS_URL, WS_KEY);
   * ```
   */

  var SceneManager = /*#__PURE__*/function () {
    /**
     * Constructor. If a url is specified, then then SceneManager will connect
     * to the specified websocket server. Otherwise, the `connect` function
     * should be called after construction.
     * @param params Optional. The scene manager configuration options
     *
     */
    function SceneManager() {
      var config = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};

      _classCallCheck(this, SceneManager);

      var _a;
      /**
       * Connection status from the Websocket.
       */


      this.connectionStatus = "disconnected";
      /**
       * List of 3d models.
       */

      this.models = [];
      /**
       * A Transport interface used to connect to a Gazebo server.
       */

      this.transport = new Transport();
      /**
       *
       */

      this.previousRenderTimestampMs = 0;
      /**
       * Name of the HTML element that will hold the rendering scene.
       */

      this.elementId = "gz-scene";
      /*
       * Whether or not lights in models are visible. Enabled by default.
       */

      this.enableLights = true;
      this.elementId = (_a = config.elementId) !== null && _a !== void 0 ? _a : "gz-scene";

      if (config.audioTopic) {
        this.audioTopic = config.audioTopic;
      }

      if (config.topicName && config.msgType && config.msgData) {
        this.topicName = config.topicName;
        this.msgType = config.msgType;
        this.msgData = config.msgData;
      }

      if (config.websocketUrl) {
        this.connect(config.websocketUrl, config.websocketKey);
      }

      if (config.enableLights !== undefined) {
        this.enableLights = config.enableLights;
      }
    }
    /**
     * Destrory the scene
     */


    _createClass(SceneManager, [{
      key: "destroy",
      value: function destroy() {
        this.disconnect();

        if (this.cancelAnimation) {
          cancelAnimationFrame(this.cancelAnimation);
        }

        this.previousRenderTimestampMs = 0;

        if (this.scene) {
          this.scene.cleanup();
        }
      }
      /**
       * Get the current connection status to a Gazebo server.
       */

    }, {
      key: "getConnectionStatus",
      value: function getConnectionStatus() {
        return this.connectionStatus;
      }
      /**
       * Get the connection status as an observable.
       * Allows clients to subscribe to this stream, to let them know when the connection to Gazebo
       * is ready for communication.
       *
       * @returns An Observable of a boolean: Whether the connection status is ready or not.
       */

    }, {
      key: "getConnectionStatusAsObservable",
      value: function getConnectionStatusAsObservable() {
        return this.transport.getConnectionStatus().pipe(rxjs.map(function (status) {
          return status === "ready";
        }));
      }
      /**
       * Change the width and height of the visualization upon a resize event.
       */

    }, {
      key: "resize",
      value: function resize() {
        if (this.scene) {
          this.scene.setSize(this.sceneElement.clientWidth, this.sceneElement.clientHeight);
        }
      }
    }, {
      key: "snapshot",
      value: function snapshot() {
        if (this.scene) {
          this.scene.saveScreenshot(this.transport.getWorld());
        }
      }
    }, {
      key: "resetView",
      value: function resetView() {
        if (this.scene) {
          this.scene.resetView();
        }
      }
    }, {
      key: "follow",
      value: function follow(entityName) {
        if (this.scene) {
          this.scene.emitter.emit("follow_entity", entityName);
        }
      }
    }, {
      key: "thirdPersonFollow",
      value: function thirdPersonFollow(entityName) {
        if (this.scene) {
          this.scene.emitter.emit("third_person_follow_entity", entityName);
        }
      }
    }, {
      key: "firstPerson",
      value: function firstPerson(entityName) {
        if (this.scene) {
          this.scene.emitter.emit("first_person_entity", entityName);
        }
      }
    }, {
      key: "moveTo",
      value: function moveTo(entityName) {
        if (this.scene) {
          this.scene.emitter.emit("move_to_entity", entityName);
        }
      }
    }, {
      key: "select",
      value: function select(entityName) {
        if (this.scene) {
          this.scene.emitter.emit("select_entity", entityName);
        }
      }
      /**
       * Publishes a message to an advertised topic.
       */

    }, {
      key: "publish",
      value: function publish() {
        if (this.scene && this.publisher) {
          var msg = this.publisher.createMessage(this.msgData);
          this.publisher.publish(msg);
        }
      }
      /**
       * Get the list of models in the scene
       * @return The list of available models.
       */

    }, {
      key: "getModels",
      value: function getModels() {
        return this.models;
      }
      /**
       * Disconnect from the Gazebo server
       */

    }, {
      key: "disconnect",
      value: function disconnect() {
        var _a, _b; // Remove the canvas. Helpful to disconnect and connect several times.


        if (((_a = this.sceneElement) === null || _a === void 0 ? void 0 : _a.childElementCount) > 0 && ((_b = this.scene.scene.renderer) === null || _b === void 0 ? void 0 : _b.domElement)) {
          this.sceneElement.removeChild(this.scene.scene.renderer.domElement);
        }

        this.transport.disconnect();
        this.sceneInfo = {};
        this.connectionStatus = "disconnected"; // Unsubscribe from observables.

        if (this.sceneInfoSubscription) {
          this.sceneInfoSubscription.unsubscribe();
        }

        if (this.particleEmittersSubscription) {
          this.particleEmittersSubscription.unsubscribe();
        }

        if (this.statusSubscription) {
          this.statusSubscription.unsubscribe();
        }
      }
      /**
       * Connect to a Gazebo server
       * @param url A websocket url that points to a Gazebo server.
       * @param key An optional authentication key.
       */

    }, {
      key: "connect",
      value: function connect(url, key) {
        var _this = this;

        this.transport.connect(url, key);
        this.statusSubscription = this.transport.getConnectionStatus().subscribe(function (response) {
          if (response === "error") {
            // TODO: Return an error so the caller can open a snackbar
            console.log("Connection failed. Please contact an administrator."); // this.snackBar.open('Connection failed. Please contact an administrator.', 'Got it');
          }

          _this.connectionStatus = response; // We can start setting up the visualization after we are Connected.
          // We still don't have scene and world information at this step.

          if (response === "connected") {
            _this.setupVisualization();
          } // Once the status is ready, we have the world and scene information
          // available.


          if (response === "ready") {
            _this.subscribeToTopics();

            if (_this.topicName) {
              _this.publisher = _this.advertise(_this.topicName, _this.msgType);
              console.log("Advertised ".concat(_this.topicName, " with msg type of\n                      ").concat(_this.msgType));
            }
          }
        }); // Scene information.

        this.sceneInfoSubscription = this.transport.sceneInfo$.subscribe(function (sceneInfo) {
          if (!sceneInfo) {
            return;
          }

          if ("sky" in sceneInfo && sceneInfo["sky"]) {
            var sky = sceneInfo["sky"]; // Check to see if a cubemap has been specified in the header.

            if ("header" in sky && sky["header"] && sky["header"]["data"]) {
              var data = sky["header"]["data"];

              for (var i = 0; i < data.length; ++i) {
                if (data[i]["key"] === "cubemap_uri" && data[i]["value"] !== undefined) {
                  _this.scene.addSky(data[i]["value"][0]);
                }
              }
            } else {
              _this.scene.addSky();
            }
          }

          _this.sceneInfo = sceneInfo;

          _this.startVisualization();

          sceneInfo["model"].forEach(function (model) {
            var modelObj = _this.sdfParser.spawnFromObj({
              model: model
            }, {
              enableLights: _this.enableLights
            });

            model["gz3dName"] = modelObj.name;

            _this.models.push(model);

            _this.scene.add(modelObj);
          });
          sceneInfo["light"].forEach(function (light) {
            var lightObj = _this.sdfParser.spawnLight(light);

            _this.scene.add(lightObj);
          }); // Set the ambient color, if present

          if (sceneInfo["ambient"] !== undefined && sceneInfo["ambient"] !== null) {
            _this.scene.ambient.color = new THREE__namespace.Color(sceneInfo["ambient"]["r"], sceneInfo["ambient"]["g"], sceneInfo["ambient"]["b"]);
          }
        });
      }
      /**
       * Advertise a topic.
       *
       * @param topic The topic to advertise.
       */

    }, {
      key: "advertise",
      value: function advertise(topic, msgTypeName) {
        return this.transport.advertise(topic, msgTypeName);
      }
      /**
       * Allows clients to subscribe to a custom topic.
       *
       * @param topic The topic to subscribe to.
       */

    }, {
      key: "subscribeToTopic",
      value: function subscribeToTopic(topic) {
        this.transport.subscribe(topic);
      }
      /**
       * Allows clients to unsubscribe from topics.
       *
       * @param name The name of the topic to unsubscribe from.
       */

    }, {
      key: "unsubscribeFromTopic",
      value: function unsubscribeFromTopic(name) {
        this.transport.unsubscribe(name);
      }
      /**
       * Play the Simulation.
       */

    }, {
      key: "play",
      value: function play() {
        this.transport.requestService("/world/".concat(this.transport.getWorld(), "/control"), "ignition.msgs.WorldControl", {
          pause: false
        });
      }
      /**
       * Pause the Simulation.
       */

    }, {
      key: "pause",
      value: function pause() {
        this.transport.requestService("/world/".concat(this.transport.getWorld(), "/control"), "ignition.msgs.WorldControl", {
          pause: true
        });
      }
      /**
       * Stop the Simulation.
       */

    }, {
      key: "stop",
      value: function stop() {
        this.transport.requestService("/server_control", "ignition.msgs.ServerControl", {
          stop: true
        });
      }
      /**
       * Subscribe to Gazebo topics required to render a scene.
       *
       * This includes:
       * - /world/WORLD_NAME/dynamic_pose/info
       * - /world/WORLD_NAME/scene/info
       */

    }, {
      key: "subscribeToTopics",
      value: function subscribeToTopics() {
        var _this2 = this;

        // Subscribe to the pose topic and modify the models' poses.
        var poseTopic = new Topic("/world/".concat(this.transport.getWorld(), "/dynamic_pose/info"), function (msg) {
          msg["pose"].forEach(function (pose) {
            var entityName = pose["name"]; // Objects created by Gz3D have an unique name, which is the
            // name plus the id.

            var entity = _this2.scene.getByName(entityName);

            if (entity) {
              _this2.scene.setPose(entity, pose.position, pose.orientation);
            } else {
              console.warn("Unable to find entity with name ", entityName, entity);
            }
          });
        });
        this.transport.subscribe(poseTopic); // Subscribe to the audio control topic.

        if (this.audioTopic) {
          new AudioTopic(this.audioTopic, this.transport);
        } // Subscribe to the 'scene/info' topic which sends scene changes.


        var sceneTopic = new Topic("/world/".concat(this.transport.getWorld(), "/scene/info"), function (sceneInfo) {
          if (!sceneInfo) {
            return;
          } // Process each model in the scene.


          sceneInfo["model"].forEach(function (model) {
            // Check to see if the model already exists in the scene. This
            // could happen when a simulation level is loaded multiple times.
            var foundIndex = _this2.getModelIndex(model["name"]); // If the model was not found, then add the new model. Otherwise
            // update the models ID.


            if (foundIndex < 0) {
              var modelObj = _this2.sdfParser.spawnFromObj({
                model: model
              }, {
                enableLights: _this2.enableLights
              });

              _this2.models.push(model);

              _this2.scene.add(modelObj);
            } else {
              // Make sure to update the exisiting models so that future pose
              // messages can update the model.
              _this2.models[foundIndex]["id"] = model["id"];
            }
          });
        });
        this.transport.subscribe(sceneTopic);
      }
      /**
       * Get the index into the model array of a model based on a name
       */

    }, {
      key: "getModelIndex",
      value: function getModelIndex(name) {
        var foundIndex = -1;

        for (var i = 0; i < this.models.length; ++i) {
          // Simulation enforces unique names between models. The ID
          // of a model may change. This occurs when levels are loaded,
          // unloaded, and then reloaded.
          if (this.models[i]["name"] === name) {
            foundIndex = i;
            break;
          }
        }

        return foundIndex;
      }
      /**
       * Setup the visualization scene.
       */

    }, {
      key: "setupVisualization",
      value: function setupVisualization() {
        var that = this; // Create a find asset helper

        function findAsset(_uri, _cb) {
          that.transport.getAsset(_uri, _cb);
        }

        this.scene = new Scene({
          shaders: new Shaders(),
          findResourceCb: findAsset
        });
        this.sdfParser = new SDFParser(this.scene);
        this.sdfParser.usingFilesUrls = true;

        if (window.document.getElementById(this.elementId)) {
          this.sceneElement = window.document.getElementById(this.elementId);
        } else {
          console.error("Unable to find HTML element with an id of", this.elementId);
        }

        this.sceneElement.appendChild(this.scene.renderer.domElement);
        this.scene.setSize(this.sceneElement.clientWidth, this.sceneElement.clientHeight);
      }
      /**
       * Animation loop.
       *
       * Renders the scene and updates any system and time-related variables.
       */

    }, {
      key: "animate",
      value: function animate() {
        var _this3 = this;

        this.cancelAnimation = requestAnimationFrame(function (timestampMs) {
          if (_this3.previousRenderTimestampMs === 0) {
            _this3.previousRenderTimestampMs = timestampMs;
          }

          _this3.animate();

          if (_this3.scene.getParticleSystem()) {
            _this3.scene.getParticleSystem().update();
          }

          _this3.scene.render(timestampMs - _this3.previousRenderTimestampMs);

          _this3.previousRenderTimestampMs = timestampMs;
        });
      }
      /**
       * Start the visualization rendering loop.
       */

    }, {
      key: "startVisualization",
      value: function startVisualization() {
        this.animate();
      }
    }]);

    return SceneManager;
  }();

  /Mobi/.test(navigator.userAgent);

  exports.Asset = Asset;
  exports.AssetViewer = AssetViewer;
  exports.AudioTopic = AudioTopic;
  exports.Color = Color;
  exports.FuelServer = FuelServer;
  exports.Gamepad = Gamepad;
  exports.Inertia = Inertia;
  exports.Material = Material;
  exports.ModelUserData = ModelUserData;
  exports.PBRMaterial = PBRMaterial;
  exports.Pose = Pose;
  exports.Publisher = Publisher;
  exports.SDFParser = SDFParser;
  exports.Scene = Scene;
  exports.SceneManager = SceneManager;
  exports.Topic = Topic;
  exports.Transport = Transport;
  exports.binaryToBase64 = binaryToBase64;
  exports.binaryToImage = binaryToImage;
  exports.getDescendants = getDescendants;

  Object.defineProperty(exports, '__esModule', { value: true });

}));
