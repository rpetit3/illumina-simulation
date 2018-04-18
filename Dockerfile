FROM rpetit3/nextconda-base
MAINTAINER robbie.petit@gmail.com

# ART Sequencing Simulator and Jellyfish
RUN conda upgrade conda \
    && conda install -y art=2016.06.05 \
    && conda install -y jellyfish=2.2.6 \
    && conda install -y biopython=1.70 \
    && conda clean --all --yes \
    && apt-get -qq -y autoremove \
    && apt-get autoclean \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/log/dpkg.log /tmp/* /var/tmp/*

# Final touches
COPY data /opt/data
COPY scripts /tmp/scripts
RUN chmod 755 /tmp/scripts/* \
    && mv /tmp/scripts/* /usr/local/bin \
    && rm -rf /tmp/*

WORKDIR /data

CMD ["illumina-simulation.py", "--help"]
