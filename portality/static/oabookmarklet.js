jQuery(document).ready(function() {

    // TODO: this bookmarklet should be updated with the code from the old project that 
    // pulls title author etc from the page the bookmarklet is opened on
    // then those useful bits of info should be shown in text input fields 
    // in a hidden panel of the bookmarklet panel below
    // if no info can be scraped, some may be returned from the oab.status call
    // but if none at all can be found, the hidden panel should open and the user 
    // should be asked to fill in the fields

    $('body').append('<div id="oabookmarkletcontainer">' +
        '<h2 id="oabookmarkletheader">Open Access Button</h2>' +
        '<div id="oabookmarklet">' +
        '<textarea class="form-control" id="oabookmarkletstory" placeholder="' +
        'Tell your story - why were you blocked? What were you trying to do at the time?" style="height:200px;width:265px;"></textarea>' +
        '<input type="checkbox" id="oabookmarkletwishlist"> add this to your wishlist' +
        '<a class="btn btn-block btn-action" href="#" id="oabookmarkletblock" style="font-size:1.1em;width:275px;"">share your open access story</a>' +
        '</div>' +
        '<div id="oabookmarkletstatus"></div>' +
        '<div id="oabookmarkletbottom"><p><a href="javascript:(function(){$(\'#oabookmarkletcontainer\').remove();})();" style="text-decoration:none;color:#f04717;">close</a></p>' +
    '</div></div>');
    $('#oabookmarkletcontainer').animate({'right':'0'},500);

    // TODO: the bookmarklet needs to know which user API KEY should actually be used
    // the last bookmarklet appeared to write this directly into the code of the bookmarklet 
    // code that the user downloaded, so perhaps we just do the same too, so when the user 
    // saves the bookmarklet from the site their API KEY is written into a var that gets passed in here
    // I (MM) will look into this further
    oab = new oabutton({
        api: 'https://openaccessbutton.org/api',
        api_key: oabuid
    });

    oab.status({
        data: {url: window.location.href},
        success: function(data) {
            // TODO: if the status query returns useful info this should be displayed
            // neatly on the oabutton bookmarklet panel
            $('#oabookmarkletstatus').html('<pre></p>' + JSON.stringify(data,"","    ") + '</p></pre>');
        }
    });
    
    var oabookmarkletblock = function(event) {
        event.preventDefault();
        // TODO: if the tp type is blocked rather than wishlist the data object 
        // below that is posted to the backend should be populated with extra data
        // so where the process above that builds the bookmarklet panel scrapes author 
        // title etc from the page, or asks the user to provide it, the values in those 
        // fields at the time the block button is pressed triggering this call
        oab['blocked']({
            data: {
                url: window.location.href
            },
            success: function() {
                $('#oabookmarklet').append('<p>Event registered</p>');
            }
        });
        if ( $('#oabookmarkletwishlist').is(':checked') ) {
            oab['wishlist']({
                data: {
                    url: window.location.href
                }
            });
        }
    }
    $('#oabookmarkletblock').bind('click',oabookmarkletblock);

});