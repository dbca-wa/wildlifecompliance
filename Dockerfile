# Prepare the base environment.
FROM ubuntu:24.04 as builder_base_wls
MAINTAINER asi@dbca.wa.gov.au
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBUG=True
ENV TZ=Australia/Perth
ENV EMAIL_HOST="smtp.corporateict.domain"
ENV DEFAULT_FROM_EMAIL='no-reply@dbca.wa.gov.au'
ENV NOTIFICATION_EMAIL='no-reply@dbca.wa.gov.au'
ENV NON_PROD_EMAIL='no-reply@dbca.wa.gov.au'
ENV PRODUCTION_EMAIL=False
ENV EMAIL_INSTANCE='DEV'
ENV SECRET_KEY="ThisisNotRealKey"
ENV SITE_PREFIX='wls-uat'
ENV SITE_DOMAIN='dbca.wa.gov.au'
ENV OSCAR_SHOP_NAME='Department of Biodiversity, Conservation and Attractions'
ENV BPAY_ALLOWED=False
ENV NODE_MAJOR=20

# For app.js, manifest.js, vendor.js versioning (default value set to 0.0.0)
ARG build_tag=0.0.0
#ENV BUILD_TAG=$build_tag
RUN echo "*************************************************** Build TAG = $build_tag ***************************************************"

# Install Python libs from base environment.
RUN apt-get clean
RUN apt-get update
RUN apt-get upgrade -y

# RUN apt-get install -yq git mercurial gcc gdal-bin libsasl2-dev libpq-dev \
#   python python-setuptools python-dev python-pip \
#   imagemagick poppler-utils \
#   libldap2-dev libssl-dev wget build-essential \
#   libmagic-dev binutils libproj-dev gunicorn tzdata \
#   mtr libevent-dev python-gevent \
#   cron rsyslog iproute2
# RUN pip install --upgrade pip
# RUN apt-get install -yq vim

RUN apt-get install --no-install-recommends -y curl wget git libmagic-dev gcc \
    binutils libproj-dev gdal-bin python3-setuptools python3-pip tzdata cron \
    rsyslog gunicorn libreoffice virtualenv 
RUN apt-get install --no-install-recommends -y libpq-dev patch
RUN apt-get install --no-install-recommends -y postgresql-client mtr htop \
    vim
RUN apt-get install --no-install-recommends -y python3-gevent \
    software-properties-common imagemagick

RUN apt-get install --no-install-recommends -y npm bzip2
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install --no-install-recommends -y python3.12 python3.12-dev
RUN apt-get install --no-install-recommends -y graphviz libgraphviz-dev pkg-config
RUN apt-get install -yq vim
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" \
    | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs

COPY timezone /etc/timezone
ENV TZ=Australia/Perth
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Default Scripts
RUN wget https://raw.githubusercontent.com/dbca-wa/wagov_utils/main/wagov_utils/bin/default_script_installer.sh -O /tmp/default_script_installer.sh
RUN chmod 755 /tmp/default_script_installer.sh
RUN /tmp/default_script_installer.sh

COPY startup.sh  /
RUN chmod 755 /startup.sh 
RUN groupadd -g 5000 oim
RUN useradd -g 5000 -u 5000 oim -s /bin/bash -d /app
RUN mkdir /app 
RUN chown -R oim.oim /app 

# Install Python libs from requirements.txt.
FROM builder_base_wls as python_libs_wls
WORKDIR /app
USER oim
RUN virtualenv /app/venv
ENV PATH=/app/venv/bin:$PATH
RUN git config --global --add safe.directory /app
COPY --chown=oim:oim requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt 
#COPY git_history_recent ./
RUN touch /app/rand_hash


# Install the project (ensure that frontend projects have been built prior to this step).
FROM python_libs_wls
COPY  --chown=oim:oim gunicorn.ini manage_wc.py ./
#COPY timezone /etc/timezone
RUN touch /app/.env
#COPY --chown=oim:oim.git ./.git
COPY --chown=oim:oim wildlifecompliance ./wildlifecompliance
RUN cd /app/wildlifecompliance/frontend/wildlifecompliance; npm install
RUN cd /app/wildlifecompliance/frontend/wildlifecompliance; npm run build
RUN python manage_wc.py collectstatic --noinput
RUN mkdir /app/wildlifecompliance/cache
RUN mkdir /app/tmp/
RUN chmod 777 /app/tmp/

EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]
CMD ["/startup.sh"]
