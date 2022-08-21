const rhea = require("rhea");

const container = rhea.connect({
    transport: 'ssl',
    host: 'localhost',
    hostname: 'jamlit',
    port: 45672,
    username: 'alice@example.net',
    password: 'secret',
    rejectUnauthorized: false,
});

container.on('connection_open', context => {
    console.log("Connected!");
});
