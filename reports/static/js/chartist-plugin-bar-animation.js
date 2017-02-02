(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD. Register as an anonymous module.
        define(['chartist', 'jquery'], function (chartist, jquery) {
            return (root.returnExportsGlobal = factory(chartist, jquery));
        });
    } else if (typeof exports === 'object') {
        // Node. Does not work with strict CommonJS, but
        // only CommonJS-like enviroments that support module.exports,
        // like Node.
        module.exports = factory(require('chartist'), require('jquery'));
    } else {
        root['Chartist.plugins.animation'] = factory(root.Chartist, root.jQuery);
    }
}(this, function (Chartist, $) {

    /**
     * This Chartist plugin provides some default animations.
     *
     */
    'use strict';

    var defaultOptions = {
        duration: 1000 // Duration of animation in milliseconds.
    };

    Chartist.plugins = Chartist.plugins || {};

    Chartist.plugins.barAnimation = function (options) {

        options = Chartist.extend({}, defaultOptions, options);

        return function animation(chart) {
            var barsAnimatedNum = 0;
            var barsNum = chart.data.series[0].length;

            chart.on('draw', function (data) {
                if (data.type === 'bar' && barsAnimatedNum < barsNum) {
                    data.element.animate({
                        y2: {
                            dur: options.duration,
                            from: data.y1,
                            to: data.y2,
                            easing: Chartist.Svg.Easing.easeOutQuint
                        },
                        opacity: {
                            dur: options.duration,
                            from: 0,
                            to: 1,
                            easing: Chartist.Svg.Easing.easeOutQuint
                        }
                    });
                    barsAnimatedNum++;
                }
            });

        };

    };
    return Chartist.plugins.barAnimation;

}));
