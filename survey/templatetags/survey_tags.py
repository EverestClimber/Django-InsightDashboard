from django import template

register = template.Library()

@register.simple_tag
def get_translation(question, lang):
    try:
        return question.translations.filter(lang=lang)[0].text
    except IndexError:
        return None
