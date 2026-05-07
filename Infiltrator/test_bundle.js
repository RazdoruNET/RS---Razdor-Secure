// Test JavaScript bundle for INFILTRATOR v2.0
// Contains obfuscated API endpoints and environment variables

(function webpackUniversalModuleDefinition(root, factory) {
    if(typeof exports === 'object' && typeof module === 'object')
        module.exports = factory();
    else if(typeof define === 'function' && define.amd)
        define([], factory);
    else if(typeof exports === 'object')
        exports["ApiClient"] = factory();
    else
        root["ApiClient"] = factory();
})(typeof self !== 'undefined' ? self : this, function() {
    return /******/ (function(modules) {
        var installedModules = {};
        
        function __webpack_require__(moduleId) {
            if(installedModules[moduleId]) {
                return installedModules[moduleId].exports;
            }
            var module = installedModules[moduleId] = {
                i: moduleId,
                l: false,
                exports: {}
            };
            modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
            module.l = true;
            return module.exports;
        }
        
        __webpack_require__.m = modules;
        __webpack_require__.c = installedModules;
        
        function __webpack_require__(moduleId) {
            return __webpack_require__(__webpack_require__.s = moduleId);
        }
        
        __webpack_require__.p = "";
        
        return __webpack_require__(__webpack_require__.s = "./src/index.js");
    })
    
    /************************************************************************/
    ([
        /* 0 */
        (function(module, exports, __webpack_require__) {
            
            // Obfuscated string array
            var _0x2a4b = [
                '\x68\x74\x74\x70\x73\x3a\x2f\x2f\x61\x70\x69\x2e\x65\x78\x61\x6d\x70\x6c\x65\x2e\x63\x6f\x6d',
                '\x2f\x61\x70\x69\x2f\x76\x31\x2f\x75\x73\x65\x72\x73',
                '\x2f\x61\x70\x69\x2f\x76\x31\x2f\x64\x61\x74\x61',
                '\x2f\x61\x70\x69\x2f\x76\x31\x2f\x61\x75\x74\x68',
                '\x70\x6f\x73\x74'
            ];
            
            // Environment variable extraction
            var config = {
                apiUrl: process.env.API_BASE_URL + _0x2a4b[0],
                timeout: parseInt(process.env.API_TIMEOUT || '5000'),
                debug: process.env.NODE_ENV === 'development'
            };
            
            // Obfuscated API client
            var _0x1f2c = function(_0x3e8d, _0x4b9a) {
                return axios['create']({
                    'baseURL': _0x3e8d,
                    'timeout': _0x4b9a,
                    'headers': {
                        'Authorization': 'Bearer ' + process.env.API_KEY,
                        'Content-Type': 'application/json'
                    }
                });
            };
            
            // API endpoint construction
            var _0x5d7e = function(_0x6a1b) {
                return config['apiUrl'] + _0x6a1b;
            };
            
            // Vulnerable endpoint calls
            var _0x7c9f = {
                getUsers: function() {
                    return _0x1f2c(_0x5d7e(_0x2a4b[1]), config['timeout'])['get']();
                },
                getUserData: function(userId) {
                    return _0x1f2c(_0x5d7e(_0x2a4b[2]), config['timeout'])['post']('/user/' + userId);
                },
                authenticate: function(credentials) {
                    return _0x1f2c(_0x5d7e(_0x2a4b[3]), config['timeout'])['post']('/auth/login', credentials);
                }
            };
            
            // Export API client
            module['exports'] = _0x7c9f;
            
        })
    /******/ ])
});
