from django import template
register = template.Library()

FULL_STAR_CLASS = "typcn-star-full-outline"
HALF_STAR_CLASS = "typcn-star-half-outline"
EMPTY_STAR_CLASS = "typcn-star-outline"


class StarRatingNode(template.Node):

    def __init__(self, rating_percent, max_stars="5"):
        self.rating = rating_percent
        self.max_stars = max_stars

    def render(self, context):
        try:
            rating = template.Variable(self.rating).resolve(context)
        except template.VariableDoesNotExist:
            rating = 0

        try:
            max_stars = template.Variable(self.max_stars).resolve(context)
        except template.VariableDoesNotExist:
            max_stars = 0

        total_halves = (max_stars - 1) * rating * 2

        html = [
            f'<div class="star-rating" title="{ 1 + (total_halves / 2):.2f} stars">'
            f'<span class="typcn {FULL_STAR_CLASS}"></span>'
        ]

        for i in range(max_stars - 1):
            if total_halves >= 2 * i + 2:
                cls = FULL_STAR_CLASS
            elif total_halves >= 2 * i + 1:
                cls = HALF_STAR_CLASS
            else:
                cls = EMPTY_STAR_CLASS

            html.append(f'<span class="typcn {cls}"></span>')

        html.append("</div>")

        return u"".join(html)


@register.tag(name='starrating')
def star_rating_tag(parser, token):
    """
    {% rating percent [max_stars=5]%}
    """
    parts = token.split_contents()
    if len(parts) <= 1:
        raise template.TemplateSyntaxError("'set' tag must be of the form: {% rating <value_percent> [<max_stars>=5] %}")

    if len(parts) <= 2:
        return StarRatingNode(parts[1])

    return StarRatingNode(parts[1], parts[2])

