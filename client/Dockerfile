FROM node:20-alpine
WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# 🔥 CRITICAL: Must tell Next.js it is Production BEFORE the build starts
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

CMD ["npm", "start"]
