# # build env
# FROM node:21.7.1-alpine
# WORKDIR /app

# COPY package*.json ./
# RUN npm install
# COPY . ./
# RUN npm run build
# RUN cp -r build result_build
# RUN npm install --global http-server
# CMD ["npx", "-y", "http-server", "-p", "8000", "/app/result_build"]

FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build
CMD cp -r build result_build
