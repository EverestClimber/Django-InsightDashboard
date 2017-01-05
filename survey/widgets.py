from django.forms.widgets import RadioSelect, RadioFieldRenderer, ChoiceInput
from django.utils.html import conditional_escape, format_html, html_safe
from django.forms.utils import flatatt
from django.utils.encoding import (
    force_str, force_text, python_2_unicode_compatible,
)
from django.utils.safestring import mark_safe

class ChoiseButton(ChoiceInput):
    def render(self, name=None, value=None, attrs=None):
        if value is None:
            value = ''

        if attrs:
            attrs_str = flatatt(attrs)
        else:
            attrs_str = ''

        return format_html(
            '''
                <button
                    type="button"
                    id="{id}"
                    class="text-left btn btn-default"
                    data-value="{choice_value}"
                    data-name="{name}"
                    {attr}>
                        <span class="cell"><i class="fa fa-check-circle" aria-hidden="true"></i></span>
                        <span class="text">{choice_label}</span>

                </button>''',
            attr=attrs_str,
            id=self.id_for_label,
            name=self.name,
            choice_value=self.choice_value,
            choice_label=self.choice_label
        )


        # if self.id_for_label:
        #     label_for = format_html(' for="{}"', self.id_for_label)
        # else:
        #     label_for = ''
        # attrs = dict(self.attrs, **attrs) if attrs else self.attrs
        # return format_html(
        #     '<label{}>{} {}</label>', label_for, self.tag(attrs), self.choice_label
        # )

class FancyRadioFieldRenderer(RadioFieldRenderer):
    outer_html = '''
        <div class="fancy-select fancy-radio {fancy_required}" data-name="{name}" id="fancy-{name}">
            <div class="fancy-alert">Required</div>
            <div class="btn-group-vertical" role="group" {id_attr}>{content}</div>
            <input id="fancy-hidden-{name}" type="hidden" name="{name}" value="{value}">
        </div>
    '''
    inner_html = '<div class="btn-group" role="group">{choice_value}</div>'
    choice_input_class = ChoiseButton
    outer_script = '''{% verbatim %}<script>
            $(document).ready(function () {
                %s
            });
        </script>{% endverbatim %}''';
    script = '''

    '''

    def render(self):
        """
        Outputs a <ul> for this set of choice fields.
        If an id was given to the field, it is applied to the <ul> (each
        item in the list will get an id of `$id_$i`).
        """
        id_ = self.attrs.get('id')
        output = []
        for i, choice in enumerate(self.choices):
            choice_value, choice_label = choice
            if isinstance(choice_label, (tuple, list)):
                attrs_plus = self.attrs.copy()
                if id_:
                    attrs_plus['id'] += '_{}'.format(i)
                sub_ul_renderer = self.__class__(
                    name=self.name,
                    value=self.value,
                    attrs=attrs_plus,
                    choices=choice_label,
                )
                sub_ul_renderer.choice_input_class = self.choice_input_class
                output.append(format_html(
                    self.inner_html, choice_value=choice_value,
                    sub_widgets=sub_ul_renderer.render(),
                ))
            else:
                w = self.choice_input_class(self.name, self.value, self.attrs.copy(), choice, i)
                output.append(format_html(self.inner_html, choice_value=force_text(w), sub_widgets=''))
        if 'required' in self.attrs:
            fancy_required = 'fancy-required'
        else:
            fancy_required = ''
        out =  format_html(
            self.outer_html,
            id_attr=format_html(' id="{}"', id_) if id_ else '',
            content=mark_safe('\n'.join(output)),
            name=self.name,
            value=self.value,
            fancy_required=fancy_required
        )
        return out
        out += self.outer_script % self.script
        return out

class FancyRadioSelect(RadioSelect):
    renderer = FancyRadioFieldRenderer
