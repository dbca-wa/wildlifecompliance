FROM ubuntu:18.04 as builder_base_wlc
MAINTAINER asi@dbca.wa.gov.au
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBUG=True
ENV TZ=Australia/Perth
ENV EMAIL_HOST="smtp.corporateict.domain"
ENV DEFAULT_FROM_EMAIL='no-reply@dbca.wa.gov.au'
ENV PRODUCTION_EMAIL=False
ENV EMAIL_INSTANCE='DEV'
ENV SECRET_KEY="ThisisNotRealKey"
ENV SITE_PREFIX="wls-uat"
ENV SITE_DOMAIN='dbca.wa.gov.au'
ENV OSCAR_SHOP_NAME='Parks & Wildlife'
ENV BPAY_ALLOWED=False

ENV FDW_MANAGER_DATABASE_URL='postgis://oim:ColumnS3ttle@aws-pgsql-002.lan.fyi/wildlifels_uat'
ENV DEFAULT_HOST="https://dev.local/"
ENV PARENT_HOST="aws-docker-001.lan.fyi"
ENV EMAIL_FROM="no-reply@dbca.wa.gov.au"
ENV HOST_PORT="9090"

ENV CMS_URL="https://oim.dbca.wa.gov.au/api/itsystems"
ENV EXT_USER_API_ROOT_URL="https://itassets.dbca.wa.gov.au"
ENV BPAY_ALLOWED=False
ENV NOTIFICATION_EMAIL="brendan.blackford@dbca.wa.gov.au"
ENV NON_PROD_EMAIL='brendan.blackford@dbca.wa.gov.au, walter.genuit@dbca.wa.gov.au, katsufumi.shibata@dbca.wa.gov.au, pauline.goodreid@dbca.wa.gov.au, norm.press@dbca.wa.gov.au, kelly.griffiths@dbca.wa.gov.au, bridgitte.reynolds@dbca.wa.gov.au, shayne.sharpe@dbca.wa.gov.au'
ENV LOG_CONSOLE_LEVEL='DEBUG'
ENV EXPLORE_PARKS_URL='https://parks-dev.dpaw.wa.gov.au'
ENV ALLOW_EMAIL_ADMINS=True

RUN apt-get update \
  && apt-get upgrade -y \
  && apt-get install -yq git mercurial gcc gdal-bin libsasl2-dev libpq-dev \
  python python-setuptools python-dev python-pip \
  imagemagick poppler-utils \
  libldap2-dev libssl-dev wget build-essential \
  libmagic-dev binutils libproj-dev tzdata
RUN pip install --upgrade pip
#RUN apt-get install -yq vim

# Install Python libs from requirements.txt.
FROM builder_base_wlc as python_libs_wlc
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
  # Update the Django <1.11 bug in django/contrib/gis/geos/libgeos.py
  # Reference: https://stackoverflow.com/questions/18643998/geodjango-geosexception-error
  && sed -i -e "s/ver = geos_version().decode()/ver = geos_version().decode().split(' ')[0]/" /usr/local/lib/python2.7/dist-packages/django/contrib/gis/geos/libgeos.py \
  && rm -rf /var/lib/{apt,dpkg,cache,log}/ /tmp/* /var/tmp/*


# Install the project (ensure that frontend projects have been built prior to this step).
FROM python_libs_wlc
COPY gunicorn.ini manage_wc.py ./
RUN touch /app/.env
COPY .git ./.git
#COPY ledger ./ledger
COPY wildlifecompliance ./wildlifecompliance
RUN python manage_wc.py collectstatic --noinput
EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]
CMD ["gunicorn", "wildlifecompliance.wsgi", "--bind", ":8080", "--config", "gunicorn.ini"]

