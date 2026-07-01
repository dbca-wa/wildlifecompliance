ARG IMAGE_TAG
ARG IMAGE_NAME
FROM ghcr.io/dbca-wa/docker-apps-dev:ubuntu_2604_base_python AS builder_base_wls
ARG IMAGE_TAG
ARG IMAGE_NAME
RUN echo "Building version: $IMAGE_TAG for $IMAGE_NAME"
ENV CONTAINER_IMAGE_TAG=${IMAGE_TAG}
ENV CONTAINER_IMAGE_NAME=${IMAGE_NAME}
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
ENV NODE_MAJOR=24

# For app.js, manifest.js, vendor.js versioning (default value set to 0.0.0)
ARG build_tag=0.0.0
#ENV BUILD_TAG=$build_tag
RUN echo "*************************************************** Build TAG = $build_tag ***************************************************"

# Replace with this mirror due to ubuntu.com mirror having issues preventing build docker build
RUN sed 's/archive.ubuntu.com/mirror.pilotfiber.com/g' /etc/apt/sources.list > /etc/apt/sourcesau.list
RUN mv /etc/apt/sourcesau.list /etc/apt/sources.list

# Install Python libs from base environment.
RUN apt-get clean
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install --no-install-recommends -y python3-gevent software-properties-common imagemagick curl

RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" \
    | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs

COPY timezone /etc/timezone
ENV TZ=Australia/Perth
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

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
ENV VIRTUAL_ENV=/app/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH=$VIRTUAL_ENV/bin:$PATH
RUN git config --global --add safe.directory /app
COPY --chown=oim:oim requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt 
#COPY git_history_recent ./
COPY python-cron ./

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
RUN python manage_wc.py script_hash_indexes --skip-checks
RUN mkdir -p /app/wildlifecompliance/cache
RUN mkdir -p /app/tmp/
RUN mkdir -p /app/session_store/


EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]
CMD ["/startup.sh"]
