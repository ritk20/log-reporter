# frontend/Dockerfile
FROM node:18-alpine

WORKDIR /app

# install dependencies
COPY package*.json ./
RUN npm ci

# copy source & build
COPY . .
RUN npm run build

# install a tiny static server
RUN npm install -g serve

# serve the production build on port 3000
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
