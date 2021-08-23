"use strict";

let args = [
    "a=1",
    "b=x",
    "c=f=1",
    "d=1",
    "e=0"
];

let kwargs = {};

console.log(111, Object.keys(kwargs).length);

for (let arg of args) {
    let [k, v] = arg.split("=", 2);
    kwargs[k] = v;
    console.log(222, Object.keys(kwargs).length, k, v);
}

console.log(333, Object.keys(kwargs).length);

console.log(JSON.stringify(kwargs, undefined, 2));

console.log(parseInt(kwargs["a"]));
console.log(new Boolean(parseInt(kwargs["d"])));
console.log(new Boolean(parseInt(kwargs["e"])));
