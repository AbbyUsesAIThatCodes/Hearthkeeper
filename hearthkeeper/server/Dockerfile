FROM ubuntu:24.04 AS build
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git python3 \
    build-essential clang cmake ninja-build libboost-all-dev default-libmysqlclient-dev \
    libssl-dev libreadline-dev zlib1g-dev libbz2-dev libncurses-dev liblzma-dev \
    default-mysql-client && rm -rf /var/lib/apt/lists/*
COPY realm.lock.json /pins.json
COPY fetch_sources.py /fetch_sources.py
RUN python3 /fetch_sources.py
ARG BUILD_JOBS=2
RUN cmake -S /src -B /build -G Ninja -DCMAKE_INSTALL_PREFIX=/opt/ac \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
    -DTOOLS_BUILD=all -DAPPS_BUILD=all -DSCRIPTS=static -DMODULES=static \
    -DWITH_WARNINGS=OFF -DBoost_USE_STATIC_LIBS=ON \
    && cmake --build /build --parallel ${BUILD_JOBS} && cmake --install /build
# Retain the SQL source tree the compiled updater expects, without optional client patches.
RUN mkdir -p /sql/modules/mod-playerbots/data /sql/modules/mod-individual-progression/data \
    && cp -a /src/data /sql/ \
    && cp -a /src/modules/mod-playerbots/data/sql /sql/modules/mod-playerbots/data/ \
    && cp -a /src/modules/mod-individual-progression/data/sql /sql/modules/mod-individual-progression/data/

FROM ubuntu:24.04 AS runtime
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 PYTHONPATH=/manager
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libmysqlclient21 libreadline8 libicu74 libssl3t64 zlib1g libbz2-1.0 \
    liblzma5 mysql-client python3 python3-pymysql python3-cryptography \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /opt/ac /opt/ac
COPY --from=build /sql /src
RUN mv /opt/ac/etc /defaults && ln -s /realm/etc /opt/ac/etc
COPY hearthkeeper /manager/hearthkeeper
WORKDIR /realm
USER 1000:1000
ENTRYPOINT ["python3", "-m", "hearthkeeper.server.container_entry"]
