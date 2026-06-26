FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

# Set default backend URL for build-time rewrites
ENV BACKEND_URL=http://backend:8082

# Build the Next.js app
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
