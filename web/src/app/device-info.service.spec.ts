import { TestBed, inject } from '@angular/core/testing';

import { DeviceInfoService } from './device-info.service';

describe('DeviceInfoService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [DeviceInfoService]
    });
  });

  it('should be created', inject([DeviceInfoService], (service: DeviceInfoService) => {
    expect(service).toBeTruthy();
  }));
});
