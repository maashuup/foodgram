# # build env
# FROM node:21.7.1-alpine
# WORKDIR /app

# COPY package*.json ./
# RUN npm install
# COPY . ./
# RUN npm run build
# RUN cp -r build result_build
# CMD ["npx", "-y", "http-server", "-p", "8000", "/app/result_build"]


# build env
FROM node:21.7.1-alpine
WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . ./
RUN npm run build
RUN cp -r build result_build
RUN npm install --global http-server
CMD ["npx", "-y", "http-server", "-p", "8000", "/app/result_build"]


# FROM node:18
# WORKDIR /app

# COPY package.json package.json
# COPY package-lock.json package-lock.json

# RUN npm ci

# COPY . .
# RUN npm run build
# RUN npm install --global http-server

# CMD ["npx", "-y", "http-server", "-p", "9000", "/app/build"]

# CMD ["sh", "-c", "http-server -p 8000 -a 0.0.0.0 /app/result_build"]
