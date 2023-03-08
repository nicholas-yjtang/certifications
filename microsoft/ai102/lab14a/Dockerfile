FROM ubuntu:20.04
RUN apt update && apt install -y curl git
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash -
RUN curl -sL https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt update && apt install -y nodejs yarn
RUN mkdir -p /opt/botframework
WORKDIR /opt/botframework
RUN git clone https://github.com/microsoft/BotFramework-Composer.git
WORKDIR /opt/botframework/BotFramework-Composer/Composer
RUN yarn; yarn build
RUN apt update  && apt install -y wget
RUN wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
RUN dpkg -i packages-microsoft-prod.deb
RUN apt update && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt install -y dotnet-sdk-3.1
ENV COMPOSER_HOST="0.0.0.0"
CMD yarn startall