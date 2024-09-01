/**
 * @fileoverview dragscroll - scroll area by dragging
 * @version 0.0.8
 *
 * @license MIT, see http://github.com/asvd/dragscroll
 * @copyright 2015 asvd <heliosframework@gmail.com>
 *
 * @FORK by Julian West, 9/12/2017: - Required use of RIGHT mouse button  - Dropped use of the 'nochilddrag' attribute  - Made code less cryptic and better commented
 *
 * The following 4 events are listened to: 'load' , 'mousemove' , 'mouseup' , 'mousedown'
 */


(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        define(['exports'], factory);
    } else if (typeof exports !== 'undefined') {
        factory(exports);
    } else {
        factory((root.dragscroll = {}));
    }
}(this, function (exports) {
    var _window = window;
    var _document = document;

    var newScrollX, newScrollY;

    var dragged = [];

    var reset = function()
	{
		var i;
		var el;

        for (i = 0; i < dragged.length;) {
            el = dragged[i++];
            el = el.container || el;
            el['removeEventListener']('mousedown', el.md, 0);
            _window['removeEventListener']('mouseup', el.mu, 0);
            _window['removeEventListener']('mousemove', el.mm, 0);
        } // end for

        // cloning into array since HTMLCollection is updated dynamically
        dragged = [].slice.call(_document.getElementsByClassName('dragscroll'));		// Locate any class named 'dragscroll'

        for (i = 0; i < dragged.length;) {
            (function(el, lastClientX, lastClientY, pushed, scroller, cont) {
                (cont = el.container || el)['addEventListener'](		// Add event listener for the mouse down
                    'mousedown',
                    cont.md = function(e)
									{
										if (e.button==2) 			// If the mousedown involves the RIGHT button.  Main change made by Julian West
										{
											// Perform the dragscroll operation
											pushed = 1;
											lastClientX = e.clientX;
											lastClientY = e.clientY;

											e.preventDefault();		// Prevent any default behavior set elsewhere
										}
									} // end of function for 'mousedown' event listener
					, 0
                );

                _window['addEventListener'](
                    'mouseup',
					cont.mu = function(e)
									{
										pushed = 0;
									}  // end of function for 'mouseup' event listener
					, 0
                );

                _window['addEventListener'](
                    'mousemove',
                    cont.mm = function(e)
									{
										if (pushed) {	// If the detected mouse move was part of a dragscroll move
											// The dragscroll move takes place here
											(scroller = el.scroller||el).scrollLeft -=
												newScrollX = (- lastClientX + (lastClientX=e.clientX));
											scroller.scrollTop -=
												newScrollY = (- lastClientY + (lastClientY=e.clientY));
											if (el == _document.body) {
												(scroller = _document.documentElement).scrollLeft -= newScrollX;
												scroller.scrollTop -= newScrollY;
											}
										}

                   					}  // end of function for 'mousemove' event listener
					, 0
                );
             })(dragged[i++]);
        }
    }


    if (_document.readyState == 'complete') {
        reset();
    } else {
        _window['addEventListener']('load', reset, 0);
    }

    exports.reset = reset;
}));