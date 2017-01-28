import jsonfield

from django.db import models


from insights.users.models import Country
from survey.models import Survey, Organization, Answer, Question, Option, Region



class Stat(models.Model):
    country = models.ForeignKey(Country, blank=True, null=True)
    survey = models.ForeignKey(Survey, null=True)
    total = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.total)


class SurveyStat(Stat):
    last = models.DateTimeField(blank=True, null=True)


class OrganizationStat(Stat):
    organization = models.ForeignKey(Organization, null=True)
    ordering = models.PositiveIntegerField('Ordering in reports', default=1, blank=True, db_index=True)

    class Meta:
        ordering = ['ordering', 'id']


class RepresentationTypeMixin(models.Model):
    TYPE_AVERAGE_PERCENT = 'type_average_percent'
    TYPE_YES_NO = 'type_yes_no'
    TYPE_MULTISELECT_TOP = 'type_multiselect_top'

    TYPE_CHOICES = (
        (TYPE_AVERAGE_PERCENT, 'Average percent representation'),
        (TYPE_YES_NO, 'Representation for "yes" or "no" answers'),
        (TYPE_MULTISELECT_TOP, 'Top 1 and top 3 representation for ordered multiselect'),

    )
    type = models.CharField('Representation Type', choices=TYPE_CHOICES, max_length=50, null=True)

    class Meta:
        abstract = True


class Representation(RepresentationTypeMixin, models.Model):
    survey = models.ForeignKey(Survey)
    question = models.ManyToManyField(Question)
    active = models.BooleanField(blank=True, default=True, db_index=True)
    ordering = models.PositiveIntegerField('Ordering in reports', default=1, blank=True, db_index=True)
    label1 = models.CharField('Label 1', max_length=400, default='', blank=True)
    label2 = models.CharField('Label 2', max_length=400, default='', blank=True)
    label3 = models.CharField('Label 3', max_length=400, default='', blank=True)

    def __str__(self):
        return "%s, %s %s %s" % (self.id, self.label1, self.label2, self.label3)

    class Meta:
        ordering = ['ordering', 'id']


class QuestionStat(RepresentationTypeMixin, models.Model):
    survey = models.ForeignKey(Survey, null=True)
    country = models.ForeignKey(Country, blank=True, null=True)
    representation = models.ForeignKey(Representation)
    data = jsonfield.JSONField()
    vars = jsonfield.JSONField()
    ordering = models.PositiveIntegerField('Ordering in reports', default=1, blank=True, db_index=True)

    report_type = 'basic'
    regions_cache = {}

    class Meta:
        ordering = ['ordering', 'id']

    @classmethod
    def get_regions(cls, country_id):
        if country_id in cls.regions_cache:
            return cls.regions_cache[country_id]

        if country_id:
            regions = list(Region.objects.filter(country_id=country_id))
        else:
            regions = list(Country.objects.filter(use_in_reports=True))
        cls.regions_cache[country_id] = regions
        return regions

    def update_type_average_percent(self):
        regions = self.get_regions(self.country_id)
        self.vars['bar_labels'] = []
        self.vars['bar_series'] = []

        data = self.data

        for reg in regions:
            reg_key = str(reg.pk)
            if reg_key in data['reg_cnt']:
                val = int(round(data['reg_sum'][reg_key] / data['reg_cnt'][reg_key]))
            else:
                val = -1
            self.vars['bar_labels'].append(reg.name.upper())
            self.vars['bar_series'].append(val)

        self.vars['pie_labels'] = [self.representation.label2, self.representation.label3]
        pers = int(round(self.data['main_sum'] / self.data['main_cnt']))
        self.vars['pie_data'] = [pers, 100-pers]
        self.vars['label1'] = self.representation.label1

    def update_type_yes_no(self):
        data = self.data
        self.vars['bar_labels'] = []
        self.vars['bar_positive_nums'] = []
        self.vars['bar_negative_nums'] = []
        regions = self.get_regions(self.country_id)
        for reg in regions:
            reg_key = str(reg.pk)
            if reg_key in data['reg_cnt']:
                positive_num = data['reg_yes'][reg_key]
                negative_num = data['reg_cnt'][reg_key] - data['reg_yes'][reg_key]
            else:
                positive_num = -1
                negative_num = -1
            self.vars['bar_labels'].append(reg.name)
            self.vars['bar_positive_nums'].append(positive_num)
            self.vars['bar_negative_nums'].append(negative_num)

        self.vars['pie_labels'] = [self.representation.label2, self.representation.label3]
        self.vars['pie_data'] = [data['main_cnt'] - data['main_yes'], data['main_yes']]
        self.vars['label1'] = self.representation.label1

    @staticmethod
    def _calculate_top(top):
        pack = []
        total = sum(top.values())
        for prop, s in top.items():
            pack.append((s, OptionDict.get(prop), 100.0 * s / total))
        pack.sort(key=lambda x: (-x[0], x[1]))
        pied = pack[:3]
        other = pack[3:]
        hide_last_legend_item = 'false'  # !! this is correct
        if other:
            other_s = sum([x[0] for x in other])
            pied.append((other_s, 'Other', 100.0 * other_s / total))
            hide_last_legend_item = 'true'  # !! this is correct

        if len(pied) < 4:
            pied += [(0, '', 0.0)] * (4-len(pied))

        data, labels, _ = zip(*pied)
        pack = pack[:10]
        out = {
            'pie': {
                'labels': labels,
                'data': data,
                'hide_last_legend_item': hide_last_legend_item
            },
            'table': pack
        }
        return out

    def update_type_multiselect_top(self):
        self.vars['label1'] = self.representation.label1
        self.vars['label2'] = self.representation.label2
        data = self.data
        self.vars['top1'] = self._calculate_top(data['top1'])
        self.vars['top3'] = self._calculate_top(data['top3'])

    def update_vars(self):
        if not self.data:
            return

        self.vars['question_text'] = self.representation.question.first().text
        if self.country_id:
            self.vars['region_name'] = self.country.name
            self.vars['header_by_country'] = 'BY REGION'
        else:
            self.vars['region_name'] = 'Europe'
            self.vars['header_by_country'] = 'BY COUNTRY'

        if not self.type:
            raise KeyError('Empty type')

        getattr(self, 'update_%s' % self.type)()

    def get_template_name(self):
        return "reports/representation/%s/%s.html" % (self.type, self.__class__.report_type)

    @classmethod
    def clear(cls):
        cls.report_type = 'basic'
        cls.regions_cache = {}


class OptionDict(models.Model):
    lower = models.CharField(max_length=200, unique=True)
    original = models.CharField(max_length=200)

    data = {}
    is_loaded = False

    @classmethod
    def clear(cls):
        cls.data = {}
        cls.is_loaded = False

    @classmethod
    def _load(cls):
        for od in cls.objects.all():
            cls.data[od.lower] = od
        cls.is_loaded = True

        for opt in Option.objects.all():
            lower = opt.value.lower()
            if lower not in cls.data:
                new_dict = cls(lower=lower, original=opt.value)
                new_dict.save()
                cls.data[lower] = new_dict
            elif opt.value != cls.data[lower].original:
                cls.data[lower].original = opt.value
                cls.data[lower].save()


    @classmethod
    def get(cls, name):
        if not cls.is_loaded:
            cls._load()
        if name in cls.data:
            return cls.data[name].original
        else:
            return name

    @classmethod
    def register(cls, lower, original):
        if not cls.is_loaded:
            cls._load()

        if lower not in cls.data:
            new_dict = cls(lower=lower, original=original)
            new_dict.save()
            cls.data[lower] = new_dict
