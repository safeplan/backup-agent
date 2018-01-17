import { Component } from '@angular/core';
import { CommaExpr } from '@angular/compiler/src/output/output_ast';
import { OnInit } from '@angular/core/src/metadata/lifecycle_hooks';
import { DeviceInfoService } from './device-info.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit{
  title = 'safeplan';
  constructor(private deviceInfoService: DeviceInfoService) { }
  ngOnInit(){
    console.log(this.deviceInfoService.getDeviceInfo())
  }

}
