import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { HttpModule }    from '@angular/http';
import { AppComponent } from './app.component';
import { DeviceInfoService } from './device-info.service';


@NgModule({
  declarations: [
    AppComponent
  ],
  imports: [
    HttpModule,
    BrowserModule
  ],
  providers: [DeviceInfoService],
  bootstrap: [AppComponent]
})
export class AppModule { }
