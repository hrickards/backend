jQuery(document).ready(function() {

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

    oab = new oabutton({
        api: 'http://localhost:5004/api',
        api_key: 'dc7a3ead-9b46-4883-b378-be4f79851f32'
    });
    oab.status({
        data: {url: window.location.href},
        success: function(data) {
            $('#oabookmarkletstatus').html('<pre></p>' + JSON.stringify(data,"","    ") + '</p></pre>');
        }
    });
    
    var oabookmarkletblock = function(event) {
        event.preventDefault();
        var tp = 'blocked';
        $('#oabookmarkletwishlist').is(':checked') ? tp = 'wishlist' : false;
        oab[tp]({
            data: {
                url: window.location.href
            },
            success: function() {
                $('#oabookmarklet').append('<p>' + tp + ' event registered</p>');
            }
        });
    }
    $('#oabookmarkletblock').bind('click',oabookmarkletblock);

});