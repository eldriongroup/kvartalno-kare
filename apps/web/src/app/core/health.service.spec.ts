import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { HealthService } from './health.service';

describe('HealthService', () => {
  let service: HealthService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(HealthService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('reports a healthy backend', () => {
    service.check();
    http.expectOne('/health').flush({ status: 'ok' });
    expect(service.state()).toBe('healthy');
  });

  it('reports an unavailable backend on error', () => {
    service.check();
    http.expectOne('/health').flush('offline', { status: 503, statusText: 'Unavailable' });
    expect(service.state()).toBe('unavailable');
  });
});
