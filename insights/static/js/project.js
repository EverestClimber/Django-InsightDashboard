function fancy_validate(name) {
    var valid = true;

    var selector;
    // console.log(name);

    if (name) {
        selector = '#fancy-' + name;
    } else {
        selector = '.fancy-required';
    }

    // console.log(selector);

    $(document).ready(function () {
        $(selector).each(function (index, element) {
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

$(document).ready(function () {

    /* HANDLE TYPES */
    setTimeout(function () {
        $("div.fancy-radio button").click(function () {
            var name = $(this).attr('data-name');
            $('#fancy-' + name + ' button').removeClass('fancy-checked');
            $(this).addClass('fancy-checked');
            $('#fancy-hidden-' + name).val($(this).attr('data-value'));
        });

        $("div.fancy-required button").click(function () {
            fancy_validate($(this).attr('data-name'));
        });

        $("div.fancy-checkbox button").click(function () {
            var id = $(this).attr('data-checkbox-for');

            var checkbox = $('#' + id);

            if (checkbox.prop('checked') == true) {
                checkbox.prop("checked", false);
                $(this).removeClass('fancy-checked');
            } else {
                checkbox.prop("checked", true);
                $(this).addClass('fancy-checked');
            }


            // $('#fancy-' + name + ' button').removeClass('fancy-checked');
            // $(this).addClass('fancy-checked');
            // $('#fancy-hidden-' + name).val($(this).attr('data-value'));
        });


        /**
         * Move selected fancy-ordered element
         * @param btn
         */
        function fancy_ordered_move(btn) {
            var checkbox = $($(btn).find('input[type="checkbox"]')[0]);

            var block = $(btn).parent();
            var name = $(btn).attr('data-name')


            if (checkbox.prop('checked') == true) {
                checkbox.prop("checked", false);
                block.detach().appendTo('#fancy-ordered-select-left-' + name);
                $(btn).removeClass('fancy-checked');
            } else {
                checkbox.prop("checked", true);
                block.detach().appendTo('#fancy-ordered-select-right-' + name);
                $(btn).addClass('fancy-checked');
            }

        }

        /**
         * Create new numeration for bages for select elements
         */
        function fancy_ordered_number_baged() {
                $("div.fancy-ordered-select div.group-right").each(function (i, element) {

                $(element).find('span.badge').each(function (j, badge) {
                    $(badge).text(j+1);
                });

            });
        }

        $("div.fancy-ordered-select button").click(function () {
            fancy_ordered_move(this);
            fancy_ordered_number_baged();
        });

        // $("div.fancy-ordered-controls button").click(function () {
        //     var id = $(this).attr('data-id');
        //     $('#' + id + ' button').each(function (i, element) {
        //         fancy_ordered_move(element);
        //     });
        //     fancy_ordered_number_baged();
        // });


        $("div.type_two_dependend_fields input.additional-switcher").change(function () {
            var id = $(this).attr('data-item-id');

            var main_input = $('#type_two_dependend_fields-main-' + id);
            if (this.checked) {
                $('#additional-' + id).show();
                main_input.val('');
                main_input.prop('disabled', true);
                if ($('#type_two_dependend_fields-main-' + id + '-error')) {
                    $('#type_two_dependend_fields-main-' + id + '-error').detach();
                    main_input.parent().parent().removeClass('has-error');
                }

            } else {
                $('#additional-' + id).hide();
                main_input.prop('disabled', false);
            }
        });


        $("div.type_yes_no button").click(function () {
            var btn = $(this);
            var id = btn.attr('data-id');

            btn.parent().find("button").removeClass('fancy-checked');
            btn.addClass('fancy-checked');
            $('#' + id).prop("checked", true);

        });

        $("div.type_yes_no_jumping button.yes").click(function () {

            var id = $(this).attr('data-question-id');
            $('#breaking-type_yes_no-'+id).show();
        });

        $("div.type_yes_no_jumping button.no").click(function () {

            var id = $(this).attr('data-question-id');
            $('#breaking-type_yes_no-'+id).hide();
        });

        var multiselect_ordered_ai=1;

        $("div.type_multiselect_ordered input.input-other").keyup(function(event){

              if ( event.which == 13 || event.which == 188) {
                var el = $(this);
                var id = el.attr('data-id');
                var val = $.trim(el.val());
                if (val[val.length - 1] == ',') {
                    val = val.substr(0, val.length-1);
                }

                var unchecked = $('#fancy-ordered-select-left-' + id + ' button[data-value="' + val + '"]');
                var checked = $('#fancy-ordered-select-right-' + id + ' button[data-value="' + val + '"]');

                if (unchecked.length) {

                    fancy_ordered_move(unchecked[ 0 ]);
                    fancy_ordered_number_baged();
                } else if (!checked.length) {

                    var template = $("#type_multiselect_ordered_option_template-"+id).clone();
                    template.removeAttr('id');

                    template.appendTo('#fancy-ordered-select-right-' + id);
                    var button = template.find('button').first();
                    var txt = template.find('.text').first();
                    var checkbox = template.find('input').first();


                    var generated_id = 'g' + multiselect_ordered_ai;
                    var option_id = 'type_multiselect_ordered-checkbox-' + generated_id;
                    multiselect_ordered_ai ++;

                    button.attr('data-value', val);
                    button.attr('data-name', id);
                    button.attr('data-checkbox-for', option_id);
                    button.click(function () {
                        fancy_ordered_move(this);
                        fancy_ordered_number_baged();
                    });
                    txt.text(val);
                    checkbox.attr('name', 'data[' + id + '][]');
                    checkbox.attr('value', val);
                    checkbox.attr('id', option_id);
                    template.removeClass('template');


                    fancy_ordered_number_baged();

                }

                el.val('');
                event.preventDefault();

              }
        });



    });


});


