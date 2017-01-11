#!/bin/bash

WORK_DIR="$(dirname "$0")"
cd $WORK_DIR/..



./manage.py dumpdata --indent 2 survey.question survey.option survey.survey survey.surveyitem survey.organization survey.hcpcategory users.country survey.region > docs/survey.json
