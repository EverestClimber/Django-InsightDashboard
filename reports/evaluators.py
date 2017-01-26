import logging

from querystring_parser import parser as queryparser

from django.db import transaction

from survey.models import Country, Survey, Organization, Answer, Question
from .models import SurveyStat, OrganizationStat, QuestionStat, Representation, OptionDict

logger = logging.getLogger(__name__)


class AbstractEvaluator(object):

    survey_stat = {}
    organization_stat = {}
    question_stat = {}
    question_representation_link = {}
    question_dict = {}


    @classmethod
    def type_average_percent_processor(cls, question_id, question_data, answer):
        q = cls.question_dict[question_id]
        if q.type != Question.TYPE_TWO_DEPENDEND_FIELDS:
            raise ValueError("type_average_percent_processor doesn't process %s", q.type)

        main_str = question_data['main'].strip()
        if not main_str:
            return

        main_float = float(main_str)
        org_id = answer.organization_id
        reg_id = answer.region_id
        country_id = answer.user.country_id
        survey_id = answer.survey_id

        r = cls.question_representation_link[question_id]

        k0 = (survey_id, None, r.pk)
        k1 = (survey_id, country_id, r.pk)
        regs = [(k0, country_id), (k1, reg_id)]

        for k, current_reg_id in regs:
            data = cls.question_stat[k].data
            if not data:
                data.update({
                    'main_sum': 0.0,
                    'main_cnt': 0,
                    'reg_sum': {},
                    'reg_cnt': {},
                    'org_sum': {},
                    'org_cnt': {}
                })

            data = cls.question_stat[k].data
            data['main_sum'] += main_float
            data['main_cnt'] += 1
            if current_reg_id in data['reg_sum']:
                data['reg_sum'][current_reg_id] += main_float
                data['reg_cnt'][current_reg_id] += 1
            else:
                data['reg_sum'][current_reg_id] = main_float
                data['reg_cnt'][current_reg_id] = 1

            if org_id in data['org_sum']:
                data['org_sum'][org_id] += main_float
                data['org_cnt'][org_id] += 1
            else:
                data['org_sum'][org_id] = main_float
                data['org_cnt'][org_id] = 1




    @classmethod
    def type_yes_no_processor(cls, question_id, question_data, answer):
        q = cls.question_dict[question_id]
        if q.type != Question.TYPE_YES_NO and q.type != Question.TYPE_YES_NO_JUMPING:
            raise ValueError("type_yes_no_processor doesn't process %s", q.type)

        result = question_data.strip()

        if result == 'Yes':
            yes = 1
        elif result == 'No':
            yes = 0
        else:
            return

        org_id = answer.organization_id
        reg_id = answer.region_id
        country_id = answer.user.country_id
        survey_id = answer.survey_id

        r = cls.question_representation_link[question_id]

        k0 = (survey_id, None, r.pk)
        k1 = (survey_id, country_id, r.pk)
        regs = [(k0, country_id), (k1, reg_id)]

        for k, current_reg_id in regs:
            data = cls.question_stat[k].data
            if not data:
                data.update({
                    'main_yes': 0,
                    'main_cnt': 0,
                    'reg_yes': {},
                    'reg_cnt': {},
                    'org_yes': {},
                    'org_cnt': {}
                })

            data = cls.question_stat[k].data
            data['main_yes'] += yes
            data['main_cnt'] += 1
            if current_reg_id in data['reg_yes']:
                data['reg_yes'][current_reg_id] += yes
                data['reg_cnt'][current_reg_id] += 1
            else:
                data['reg_yes'][current_reg_id] = yes
                data['reg_cnt'][current_reg_id] = 1

            if org_id in data['org_yes']:
                data['org_yes'][org_id] += yes
                data['org_cnt'][org_id] += 1
            else:
                data['org_yes'][org_id] = yes
                data['org_cnt'][org_id] = 1


    @classmethod
    def type_multiselect_top_processor(cls, question_id, question_data, answer):
        q = cls.question_dict[question_id]
        if q.type != Question.TYPE_MULTISELECT_ORDERED:
            raise ValueError("type_multiselect_top_processor doesn't process %s", q.type)

        if not question_data or '' not in question_data:
            return

        options = question_data['']
        if not options:
            return

        top3 = []

        for i, opt in enumerate(options):
            opt = opt.strip()
            if not opt:
                continue

            lower = opt.lower()
            OptionDict.register(lower, opt)

            if not i:
                top1 = lower

            if lower not in top3:
                top3.append(lower)
            if len(top3) == 3:
                break

        r = cls.question_representation_link[question_id]
        org_id = answer.organization_id
        country_id = answer.user.country_id
        survey_id = answer.survey_id
        k0 = (survey_id, None, r.pk)
        k1 = (survey_id, country_id, r.pk)

        for k in [k0, k1]:
            data = cls.question_stat[k].data
            if not data:
                data.update({
                    'cnt': 0,
                    'top1': {},
                    'top3': {},
                    'org': {},
                })

            data['cnt'] += 1

            if org_id not in data['org']:
                data['org'][org_id] = {
                    'cnt': 0,
                    'top1': {},
                    'top3': {},
                }

            data['org'][org_id]['cnt'] += 1

            if top1 in data['top1']:
                data['top1'][top1] += 1
            else:
                data['top1'][top1] = 1

            if top1 in data['org'][org_id]['top1']:
                data['org'][org_id]['top1'][top1] += 1
            else:
                data['org'][org_id]['top1'][top1] = 1


            for top_i in top3:
                if top_i in data['top3']:
                    data['top3'][top_i] += 1
                else:
                    data['top3'][top_i] = 1

                if top_i in data['org'][org_id]['top3']:
                    data['org'][org_id]['top3'][top_i] += 1
                else:
                    data['org'][org_id]['top3'][top_i] = 1








    @staticmethod
    def get_answers():
        raise NotImplementedError


    @staticmethod
    def clear():
        raise NotImplementedError

    @classmethod
    def load_stat(cls):
        surveys = SurveyStat.objects.all()
        for survey in surveys:
            cls.survey_stat[(survey.survey_id, survey.country_id)] = survey

        orgs = OrganizationStat.objects.all()
        for org in orgs:
            cls.organization_stat[(org.survey_id, org.country_id, org.organization_id)] = org

        quests = QuestionStat.objects.all()
        for quest in quests:
            cls.question_stat[(quest.survey_id, quest.country_id, quest.representation_id)] = quest

    @classmethod
    def fill_out(cls):
        countries = list(Country.objects.all())
        countries.append(None)
        organizations = list(Organization.objects.all())
        representations = list(Representation.objects.prefetch_related('question').filter(active=True))

        for surv in Survey.objects.filter(active=True):
            for country in countries:
                # Fill out survey stat
                if country is None:
                    country_id = country
                else:
                    country_id = country.pk
                surv_key = (surv.pk, country_id)

                if surv_key not in cls.survey_stat:
                    cls.survey_stat[surv_key] = SurveyStat(survey=surv, country=country)

                # Fill out organizations stat
                for org in organizations:
                    org_key = (surv.pk, country_id, org.pk)
                    if org_key not in cls.organization_stat:
                        cls.organization_stat[org_key] = OrganizationStat(
                            survey=surv, country=country, organization=org, ordering=org.ordering)
                    else:
                        if cls.organization_stat[org_key].ordering != org.ordering:
                            cls.organization_stat[org_key].ordering = org.ordering

                # Fill out question stat
                for repr in representations:
                    q_key = (surv.pk, country_id, repr.pk)
                    if q_key not in cls.question_stat:
                        cls.question_stat[q_key] = QuestionStat(
                            survey=surv, country=country, representation=repr, ordering=repr.ordering, type=repr.type)
                    else:
                        if cls.question_stat[q_key].ordering != repr.ordering:
                            cls.question_stat[q_key].ordering = repr.ordering

                    # Fill out question representation links
                    questions = repr.question.all()
                    for q in questions:
                        cls.question_representation_link[q.pk] = repr
                        if q.pk not in cls.question_dict:
                            cls.question_dict[q.pk] = q



    @classmethod
    def update_survey_stat(cls, surv_key, answer):
        survey_id, country_id = surv_key
        if surv_key not in cls.survey_stat:
            cls.survey_stat[surv_key] = SurveyStat(survey_id=survey_id, country_id=country_id, last=answer.created_at)
        cls.survey_stat[surv_key].total += 1
        if cls.survey_stat[surv_key].last:
            cls.survey_stat[surv_key].last = max(cls.survey_stat[surv_key].last, answer.created_at)
        else:
            cls.survey_stat[surv_key].last = answer.created_at

        surv_key_all = (survey_id, None)
        if surv_key_all not in cls.survey_stat:
            cls.survey_stat[surv_key_all] = SurveyStat(survey_id=survey_id, country_id=None)
        cls.survey_stat[surv_key_all].total += 1
        if cls.survey_stat[surv_key_all].last:
            cls.survey_stat[surv_key_all].last = max(cls.survey_stat[surv_key].last, answer.created_at)
        else:
            cls.survey_stat[surv_key_all].last = answer.created_at

    @classmethod
    def update_organization_stat(cls, org_key):
        survey_id, country_id, organization_id = org_key
        if org_key not in cls.organization_stat:
            cls.organization_stat[org_key] = OrganizationStat(
                survey_id=survey_id, country_id=country_id, organization_id=organization_id)
        cls.organization_stat[org_key].total += 1

        org_key_all = (survey_id, None, organization_id)
        if org_key_all not in cls.organization_stat:
            cls.organization_stat[org_key_all] = OrganizationStat(
                survey_id=survey_id, country_id=None, organization_id=organization_id)
        cls.organization_stat[org_key_all].total += 1

    @staticmethod
    def parse_query_string(string):
        return queryparser.parse(string)


    @classmethod
    def process_answer(cls, answer):
        if not answer.body:
            raise KeyError("There is no answers data")

        results = cls.parse_query_string(answer.body)
        if 'data' not in results:
            raise KeyError("There is data in post results")

        data = results['data']
        if type(data) != dict:
            raise KeyError("Answer data should be dict")

        for qid, question_data in data.items():
            if qid not in cls.question_dict:
                logger.warning("Question %s is not expected" % qid)
                continue
            if qid not in cls.question_representation_link:
                logger.warning("Question %s is not connected to any of representations" % qid)
                continue
            repr = cls.question_representation_link[qid]
            processor = "%s_processor" % repr.type
            getattr(cls, processor)(qid, question_data, answer)

        survey_id = answer.survey_id
        country_id = answer.user.country_id
        organization_id = answer.organization_id

        surv_key = (survey_id, country_id)
        cls.update_survey_stat(surv_key, answer)

        org_key = (survey_id, country_id, organization_id)
        cls.update_organization_stat(org_key)

        answer.is_updated = True
        answer.save(update_fields=['is_updated'])


    @classmethod
    def save(cls):
        for surv_stat in cls.survey_stat.values():
            surv_stat.save()
        for org_stat in cls.organization_stat.values():
            org_stat.save()
        for quest_stat in cls.question_stat.values():
            quest_stat.save()





    @classmethod
    @transaction.atomic
    def process_answers(cls):
        cls.clear()
        cls.load_stat()
        cls.fill_out()
        answers = cls.get_answers()
        for answer in answers:
            try:
                cls.process_answer(answer)
            except Exception as e:
                logger.warning("Answer can't be processed. Exception: %s" % e)


        cls.save()

    def evaluate(self):
        pass


class TotalEvaluator(AbstractEvaluator):
    @staticmethod
    def get_answers():
        return Answer.objects.all()

    @staticmethod
    def clear():
        SurveyStat.objects.all().delete()
        OrganizationStat.objects.all().delete()
        QuestionStat.objects.all().delete()


class LastEvaluator(AbstractEvaluator):
    @staticmethod
    def get_answers():
        return Answer.objects.filter(is_updated=False)

    @staticmethod
    def clear():
        pass

