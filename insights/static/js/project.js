/* Project specific Javascript goes here. */

/*
Formatting hack to get around crispy-forms unfortunate hardcoding
in helpers.FormHelper:

    if template_pack == 'bootstrap4':
        grid_colum_matcher = re.compile('\w*col-(xs|sm|md|lg|xl)-\d+\w*')
        using_grid_layout = (grid_colum_matcher.match(self.label_class) or
                             grid_colum_matcher.match(self.field_class))
        if using_grid_layout:
            items['using_grid_layout'] = True

Issues with the above approach:

1. Fragile: Assumes Bootstrap 4's API doesn't change (it does)
2. Unforgiving: Doesn't allow for any variation in template design
3. Really Unforgiving: No way to override this behavior
4. Undocumented: No mention in the documentation, or it's too hard for me to find
*/
// $('.form-group').removeClass('row');

$(document).ready(function () {
    // if ($('#hidden-{name}') && $('#hidden-{name}').attr('value')){
    //     console.log('test');
    // }

    $( "div.fancy-select" ).each(function( index, element ) {
        var name = $( this ).attr('data-name');
        var hidden_id = '#fancy-hidden-' + name;
        if ($(hidden_id) && $(hidden_id).attr('value')){
            console.log('test');
        }

        console.log( index + ": " + $( this ).attr('data-name') );
    });

    $("div.fancy-radio button").click(function(){
        var name = $(this).attr('data-name');
        $('#fancy-' + name + ' button').removeClass('fancy-checked');
        $(this).addClass('fancy-checked');
        $('#fancy-hidden-' + name).val($(this).attr('data-value'));
    });

    $("div.fancy-required button").click(function(){
        fancy_validate($(this).attr('data-name'));
    });

});


function fancy_validate(name) {
    var valid = true

    var selector
    console.log(name);

    if (name) {
        selector = '#fancy-' + name;
    } else {
        selector = '.fancy-required';
    }

    console.log(selector);

    $(document).ready(function () {
        $(selector).each(function(index, element){
            var hiddens = $(element).find('input[type="hidden"]');

            if (hiddens.length) {
                var hidden = hiddens[0];
                if ($(hidden).val() == '') {
                    $(element).addClass('fancy-invalid-required');
                    valid = false;
                } else {
                    $(element).removeClass('fancy-invalid-required');
                }
            }

        });
    });

    return valid;
}
