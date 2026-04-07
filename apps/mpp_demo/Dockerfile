FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev

COPY server.mjs ./

ENV PORT=3001

EXPOSE 3001

CMD ["node", "server.mjs"]
