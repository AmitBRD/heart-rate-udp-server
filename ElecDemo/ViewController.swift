//
//  ViewController.swift
//  ElecDemo
//
//  Created by NhatHM on 8/9/19.
//  Copyright © 2019 GST.PID. All rights reserved.
//

import UIKit
import Network

class ViewController: UIViewController {

    let udpFetch = UDPFetcher()
    
    override func viewDidLoad() {
        super.viewDidLoad()
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        WorkoutTracking.shared.authorizeHealthKit()
        WorkoutTracking.shared.observerHeartRateSamples()
        WatchKitConnection.shared.delegate = self
    }
}

extension ViewController: WatchKitConnectionDelegate {
    func didFinishedActiveSession() {
        WatchKitConnection.shared.sendMessage(message: ["username" : "nhathm" as AnyObject])
    }
    
    func uploadData(message: [String : Any]) {
        if let jsonData = try? (JSONSerialization.data(withJSONObject: message, options: [])){
            if let jsonString = String(data: jsonData, encoding: .utf8) {
                print(jsonString)
                udpFetch.sendUDP(jsonString)
            }
        }
        
       
    }
}
