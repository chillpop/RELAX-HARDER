var noble = require('noble');
var readline = require('readline');

var serviceUUID = 'F9BB83582069437EA3D70BF0E1870F7D'.toLowerCase();
var characteristicUUID = '30D4E7E20CCE40FEB5DD6565D9BBFF8B'.toLowerCase();

var serialPeripheral;
var serialCharacteristic;

var logError = function(error) {
  if (error) {
    console.log('error: ' + error);
  }
};

noble.on('stateChange', function(state) {
  console.log('on -> stateChange: ' + state);

  if (state === 'poweredOn') {
    //start scanning for the service we're interested in, not allowing duplicates
    console.log('Begin scanning for service: ' +  serviceUUID);
    noble.startScanning([serviceUUID]);
    // noble.startScanning();
  } else {
    noble.stopScanning();
  }
});

noble.on('discover', function(peripheral) {
  console.log('peripheral discovered (' + peripheral.uuid+ '):');
  console.log('\thello my local name is:');
  console.log('\t\t' + peripheral.advertisement.localName);
  console.log('\tcan I interest you in any of the following advertised services:');
  console.log('\t\t' + JSON.stringify(peripheral.advertisement.serviceUuids));

  if (peripheral.advertisement.serviceUuids.indexOf(serviceUUID) == -1) {
    console.log('the discovered peripheral does not have the required service.');
    process.exit(0);
  }

  //save the peripheral for later
  serialPeripheral = peripheral;
  peripheral.connect(function(error) {
    logError(error);
    console.log('connected to peripheral');

    peripheral.discoverServices([serviceUUID], function(error, services) {
      logError(error);
      var service = services[0];
      console.log('discovered service ' + service);

      service.discoverCharacteristics([characteristicUUID], function(error, characteristics) {
        logError(error);
        var characteristic = characteristics[0];
        console.log('discovered characteristic ' + characteristic + ' with uuid ' + characteristic.uuid);

        //save the characteristic for later
        serialCharacteristic = characteristic;

        noble.stopScanning();
        listenForInput();
      })
    })
  })
});

var listenForInput = function() {
  var input = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  input.setPrompt('>');
  input.prompt();
  input.on('line', function(line) {
    data = line.trim();
    if (data === 'q') {
      input.close();
      serialPeripheral.disconnect();
      process.exit(0);
    } else {
      var buffer = new Buffer(data);
      serialCharacteristic.write(buffer, true, function(err) {
        if (err) {
          console.log('error writing to service: '+ err);
        } else {
          console.log('successfully wrote to service');
        }
      });
      console.log(data);
    }
      input.prompt();
  });
}