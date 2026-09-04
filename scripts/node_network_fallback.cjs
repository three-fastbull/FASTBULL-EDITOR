// Some sandboxed/locked-down Windows environments deny network-interface
// enumeration. Remotion only needs a usable local address, so provide loopback
// when Node's native call throws. Normal systems keep their real interfaces.
const os = require('node:os');
const original = os.networkInterfaces.bind(os);
os.networkInterfaces = () => {
  try {
    return original();
  } catch (_) {
    return {
      lo: [{address: '127.0.0.1', netmask: '255.0.0.0', family: 'IPv4', mac: '00:00:00:00:00:00', internal: true, cidr: '127.0.0.1/8'}],
    };
  }
};
