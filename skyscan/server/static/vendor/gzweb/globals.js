/*
 * Maps the browser builds of gzweb's dependencies onto the global names the gzweb UMD bundle expects, and works
 * around one gz-launch websocket-server bug.
 *
 * The server answers "protos" with the .proto definitions of every message, but it leaves out the two TOP-LEVEL enums
 * of gz-msgs10 (PixelFormatType, SphericalCoordinatesType). Any scene containing a camera sensor then fails to decode
 * with "no such Type or Enum '.gz.msgs.PixelFormatType' in Type .gz.msgs.CameraSensor". We append the two enums
 * (copied from gz-msgs10 image.proto / spherical_coordinates.proto) when the served text lacks them.
 */
(function (g) {
  g.eventemitter2 = { EventEmitter2: g.EventEmitter2 };
  g['fast-xml-parser'] = g.fxp;
  g['three-nebula'] = g.Nebula;
  g.protobufjs = g.protobuf;

  var MISSING_TOP_LEVEL_ENUMS = {
    PixelFormatType:
      'enum PixelFormatType { UNKNOWN_PIXEL_FORMAT = 0; L_INT8 = 1; L_INT16 = 2; RGB_INT8 = 3; RGBA_INT8 = 4; ' +
      'BGRA_INT8 = 5; RGB_INT16 = 6; RGB_INT32 = 7; BGR_INT8 = 8; BGR_INT16 = 9; BGR_INT32 = 10; R_FLOAT16 = 11; ' +
      'RGB_FLOAT16 = 12; R_FLOAT32 = 13; RGB_FLOAT32 = 14; BAYER_RGGB8 = 15; BAYER_BGGR8 = 16; BAYER_GBRG8 = 17; ' +
      'BAYER_GRBG8 = 18; }',
    SphericalCoordinatesType:
      'enum SphericalCoordinatesType { SPHERICAL = 0; ECEF = 1; GLOBAL = 2; LOCAL = 3; LOCAL2 = 4; }',
  };

  var originalParse = g.protobuf.parse;
  g.protobuf.parse = function (source) {
    var args = Array.prototype.slice.call(arguments);
    if (typeof source === 'string' && source.indexOf('package gz.msgs;') !== -1) {
      var extra = '';
      Object.keys(MISSING_TOP_LEVEL_ENUMS).forEach(function (name) {
        if (!new RegExp('^\\s*enum\\s+' + name + '\\b', 'm').test(source)) extra += '\n' + MISSING_TOP_LEVEL_ENUMS[name];
      });
      if (extra) args[0] = source + '\n' + extra + '\n';
    }
    return originalParse.apply(this, args);
  };
})(window);
